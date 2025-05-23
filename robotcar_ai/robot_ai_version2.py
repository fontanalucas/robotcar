import time
import numpy as np
import polars as pl
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import os
import cv2
from mlagents_envs.environment import UnityEnvironment
from mlagents_envs.side_channel.engine_configuration_channel import EngineConfigurationChannel
from mlagents_envs.base_env import ActionTuple

# Client ML-Agents
class SimulatorClient:
    def __init__(self, env_path=None, worker_id=0):  # None = Unity Editor
        self.channel = EngineConfigurationChannel()
        print("Connexion à Unity Editor en cours...")
        try:
            self.env = UnityEnvironment(
                file_name=env_path,
                base_port=5004,
                worker_id=worker_id,
                side_channels=[self.channel]
            )
            print("Connexion réussie !")
            self.env.reset()
            self.behavior_names = list(self.env.behavior_specs.keys())
            if not self.behavior_names:
                raise RuntimeError("Aucun comportement détecté. Vérifie l'Agent dans la scène Unity.")
            self.behavior_name = self.behavior_names[0]
            spec = self.env.behavior_specs[self.behavior_name]
            print(f"Comportement : {self.behavior_name}, Actions : {spec.action_spec.continuous_size}")
            self.num_rays = 10
        except Exception as e:
            print(f"❌ Erreur de connexion à Unity Editor : {e}")
            raise

    def set_controls(self, speed, steering):
        try:
            decision_steps, _ = self.env.get_steps(self.behavior_name)
            if len(decision_steps) == 0:
                print("Aucun agent actif pour recevoir une action.")
                return
            action = ActionTuple(continuous=np.array([[speed, steering]], dtype=np.float32))
            self.env.set_actions(self.behavior_name, action)
            self.env.step()
            print(f"Commande envoyée : speed={speed:.2f}, steering={steering:.2f}")
        except Exception as e:
            print(f"Erreur lors de l'envoi des commandes : {e}")

    def get_observations(self):
        decision_steps, _ = self.env.get_steps(self.behavior_name)
        if len(decision_steps) > 0:
            obs = decision_steps.obs[0][0]
            pos_values = obs[:3]
            ray_values = obs[3:3 + self.num_rays]
            return pos_values, ray_values
        return None, None

    def get_position(self):
        pos, _ = self.get_observations()
        return f"OK:POS:{pos[0]}:{pos[1]}:{pos[2]}" if pos is not None else "TIMEOUT"

    def get_raycast_info(self):
        _, rays = self.get_observations()
        return f"OK:RAYS:{':'.join(map(str, rays))}" if rays is not None else "TIMEOUT"

    def get_speed(self):
        return "OK:SPEED:0.0"

    def get_steering(self):
        return "OK:STEERING:0.0"

    def close(self):
        self.env.close()

# Input Manager sans pynput (OpenCV based fallback)
class InputManager:
    def __init__(self):
        self.speed = 0.0
        self.steering = 0.0
        self.running = True
        print("Utilise Z/S pour avancer/reculer, Q/D pour tourner. Echap pour quitter.")

    def update(self):
        key = cv2.waitKey(1) & 0xFF
        if key == ord('z'):
            self.speed = min(self.speed + 0.1, 1.0)
        elif key == ord('s'):
            self.speed = max(self.speed - 0.1, -1.0)
        elif key == ord('q'):
            self.steering = max(self.steering - 0.1, -1.0)
        elif key == ord('d'):
            self.steering = min(self.steering + 0.1, 1.0)
        elif key == 27:  # Echap
            self.running = False
        elif key != 255:
            print(f"Touche non utilisée : {chr(key)}")

    def get_inputs(self):
        return self.speed, self.steering

    def is_running(self):
        return self.running


class DataCollector:
    def __init__(self, num_rays=10):
        self.data = []
        self.num_rays = num_rays

    def collect(self, client, speed, steering):
        position = client.get_position()
        raycast = client.get_raycast_info()
        if "OK" in position and "OK" in raycast:
            pos_values = position.split(":")[2:]
            ray_values = raycast.split(":")[2:]
            self.data.append(pos_values + ray_values + [speed, steering])

    def save(self, filename="driving_data.csv"):
        columns = [f"pos_{i}" for i in range(3)] + [f"ray_{i}" for i in range(self.num_rays)] + ["speed", "steering"]
        new_df = pl.DataFrame({col: [row[i] for row in self.data] for i, col in enumerate(columns)})
        print(f"Nouvelles données à ajouter : {len(new_df)} lignes")
        if os.path.exists(filename):
            existing_df = pl.read_csv(filename)
            print(f"Données existantes : {len(existing_df)} lignes")
            combined_df = pl.concat([existing_df, new_df])
            combined_df.write_csv(filename)
            print(f"Données ajoutées à {filename} (total : {len(combined_df)} lignes)")
        else:
            new_df.write_csv(filename)
            print(f"Nouveau fichier créé : {filename} ({len(new_df)} lignes)")
        self.data = []

class RobocarAI:
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=200, random_state=42)
        self.feature_names = [f"pos_{i}" for i in range(3)] + [f"ray_{i}" for i in range(10)]
        self.max_speed = 0.4

    def train(self, filename="driving_data.csv"):
        df = pl.read_csv(filename).with_columns([
            pl.col(col).cast(pl.Float64) for col in ["speed", "steering"] + self.feature_names
        ])
        df = df.drop_nulls()
        X = df.select(self.feature_names).to_numpy()
        y = df.select(["speed", "steering"]).to_numpy()
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        self.model.fit(X_train, y_train)
        y_pred = self.model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        print(f"Erreur quadratique moyenne (MSE) : {mse}")

    def predict(self, client):
        position = client.get_position()
        raycast = client.get_raycast_info()
        if "OK" in position and "OK" in raycast:
            pos_values = [float(val) for val in position.split(":")[2:]]
            ray_values = [float(val) for val in raycast.split(":")[2:]]
            inputs = np.array([pos_values + ray_values])
            speed, steering = self.model.predict(inputs)[0]
            min_ray = min(ray_values)
            if min_ray < 50:
                speed = 0.0
            elif min_ray < 150:
                speed = min(speed, 0.3)
            elif min_ray < 250:
                speed = min(speed, 0.5)
            speed = min(speed, self.max_speed)
            steering = max(min(steering, 1.0), -1.0)
            print(f"Adjusted - speed: {speed:.2f}, steering: {steering:.2f}, min_ray: {min_ray:.2f}")
            return speed, steering
        return 0.0, 0.0

def analyze_data(filename="driving_data.csv"):
    df = pl.read_csv(filename)
    print("Nombre de lignes :", len(df))
    print("Aperçu des données :\n", df.head())
    print("Statistiques :\n", df.describe())

def main():
    client = SimulatorClient(env_path=None)
    input_manager = InputManager()
    collector = DataCollector(num_rays=client.num_rays)
    ai = RobocarAI()

    mode = input("Mode (manual/ai/train/analyze) : ").lower()

    if mode == "manual":
        print("Conduite manuelle. Utilise Z/S pour avancer/reculer, Q/D pour tourner.")
        while input_manager.is_running():
            input_manager.update()
            speed, steering = input_manager.get_inputs()
            client.set_controls(speed, steering)
            collector.collect(client, speed, steering)
            time.sleep(0.02)

            if int(time.time() * 100) % 100 == 0:
                current_time = time.time()
                print(f"Fréquence : {1 / (current_time - last_time):.1f} Hz")
                last_time = current_time
        collector.save()

    elif mode == "train":
        ai.train()
        print("Entraînement terminé.")

    elif mode == "ai":
        ai.train()
        print("Mode IA activé.")
        while True:
            speed, steering = ai.predict(client)
            client.set_controls(speed, steering)
            collector.collect(client, speed, steering)
            time.sleep(0.001)

    elif mode == "analyze":
        analyze_data()
        print("Analyse terminée.")

    else:
        print("Mode invalide. Choisis parmi : manual, ai, train, analyze")

    client.close()

if __name__ == "__main__":
    main()
