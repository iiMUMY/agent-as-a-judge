import numpy as np


def train_q_learning(num_episodes=100):
    q_table = np.zeros((25, 4))
    episodes = list(range(num_episodes))
    returns = [0.0 for _ in episodes]
    return q_table, episodes, returns


def save_outputs():
    learning_curve_path = "results/figures/learning_curve.png"
    path_changes_path = "results/figures/path_changes.gif"
    model_path = "models/saved_models/q_learning_model.npy"
    return learning_curve_path, path_changes_path, model_path
