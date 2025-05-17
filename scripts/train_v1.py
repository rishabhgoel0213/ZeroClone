# import os
# import random
# import sys
# import time
# import datetime
# import argparse

# import queue
# import multiprocessing as mp
# from multiprocessing import Manager, Process, Queue
# mp.set_start_method("spawn", force=True)

# import re
# import numpy as np
# import torch
# import torch.nn as nn
# from torch.utils.data import random_split, DataLoader

# import network
# from chess import play_bots


# CHECKPOINT_RE = re.compile(r"value_(\d{8}_\d{6})\.pth$")
# DATASETS = "/workspaces/alphazero-dev/ValueNetMCTS/models/value/datasets_v1"
# CHECKPOINTS = "/workspaces/alphazero-dev/ValueNetMCTS/models/value/checkpoints_v1"
# DATASET_LATEST = "/workspaces/alphazero-dev/ValueNetMCTS/models/value/dataset_latest.npz"
# MODEL_LATEST = "/workspaces/alphazero-dev/ValueNetMCTS/models/value/value_latest.pth"


# """
# Self play background task that gets multithreaded
# """
# def worker(stats, lock, result_queue, model, simulations, c, policy_freedom):
#     while True:
#         outcome, data = play_bots(model, model, simulations, c, policy_freedom)
#         with lock:
#             stats['total'] += 1
#             if outcome == 'draw':
#                 stats['draws'] += 1
#             elif outcome == 'white':
#                 stats['white_wins'] += 1
#             else:
#                 stats['black_wins'] += 1
#         result_queue.put(data)

# """
# Simple extra task to print out aggregated statistics for debugging
# """
# def stats_printer(stats, interval=5):
#     while True:
#         time.sleep(interval)
#         print(f"[Stats] total={stats['total']} | draws={stats['draws']} | white_wins={stats['white_wins']} | black_wins={stats['black_wins']}")

# """
# Dataset generation logic with multithreading
# Runs that actual self play logic many times in parallel to create the dataset
# Returns formatted numpy arrays to train the value net on
# """
# def generate_dataset(num_games=2000, simulations=1000, c=1.4, policy_freedom=0, num_workers=mp.cpu_count()):
#     manager = Manager()
#     stats = manager.dict(total=0, draws=0, white_wins=0, black_wins=0)
#     lock = manager.Lock()
#     result_queue = Queue()
#     model = network.ValueNetwork() if not os.path.exists(MODEL_LATEST) else torch.load(MODEL_LATEST, map_location="cpu")

#     workers = []
#     for _ in range(num_workers):
#         p = Process(target=worker, args=(stats, lock, result_queue, model, simulations, c, policy_freedom), daemon=True)
#         p.start()
#         workers.append(p)

#     stats_printer_proc = Process(target=stats_printer, args=(stats, 15), daemon=True)
#     stats_printer_proc.start()

#     master_states = []
#     master_results = []

#     try:
#         while True:
#             time.sleep(1)
#             if stats['total'] >= num_games:
#                 print(f"Reached {stats['total']} games—shutting down.")
#                 break
#     except KeyboardInterrupt:
#         print("Interrupted by user—shutting down.")
#         sys.exit(0)
#     finally:
#         stats_printer_proc.terminate()
#         stats_printer_proc.join()
#         for w in workers:
#             w.terminate()
#             w.join()

#     try:
#         while True:
#             item = result_queue.get_nowait()
#             master_states.extend(item['states'])
#             master_results.extend(item['results'])
#     except queue.Empty:
#         pass
            

#     states = np.stack(master_states, axis=0)
#     results = np.array(master_results, dtype=np.float32)

#     if os.path.exists(DATASET_LATEST):
#         ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
#         archived = f'{DATASETS}/dataset_{ts}.npz'
#         os.rename(DATASET_LATEST, archived)

#     np.savez(DATASET_LATEST, states=states, results=results)

#     return states, results, stats

# """
# Actual training logic for the value network
# Uses generated dataset as training data
# Returns new model as well as test loss
# """
# def train_and_eval(states, results):
#     dataset = network.ChessStateDataset(states, results)

#     train_size = int(0.8 * len(dataset))
#     test_size  = len(dataset) - train_size

#     train_ds, test_ds = random_split(dataset, [train_size, test_size])

#     train_loader = DataLoader(train_ds, batch_size=64, shuffle=True, num_workers=4)
#     test_loader = DataLoader(test_ds, batch_size=64, shuffle=True, num_workers=4)


#     model = network.ValueNetwork() if not os.path.exists(MODEL_LATEST) else torch.load(MODEL_LATEST, map_location="cpu")
#     network.train(model, train_loader, epochs=1, lr=1e-3, device='cuda')

#     def test_loss(model, test_loader):
#         model.eval()
#         criterion = nn.MSELoss()
#         total_loss = 0.0
#         with torch.no_grad():
#             for states, targets in test_loader:
#                 states, targets = states.to('cuda'), targets.to('cuda').unsqueeze(1)
#                 outputs = model(states)
#                 loss    = criterion(outputs, targets)
#                 total_loss += loss.item() * states.size(0)
#         return total_loss / len(test_loader.dataset)
    
#     loss = test_loss(model, test_loader)
#     print("Test Loss:", loss)

#     return model, loss


# def worker2(latest_wins, total, lock, model, prev_model):
#     while True:
#         model_white = model
#         model_black = prev_model
#         latest_is_white = True
#         if random.random() < 0.5:
#             model_white, model_black = model_black, model_white
#             latest_is_white = False

#         outcome, _ = play_bots(model_white, model_black)
#         with lock:
#             total += 1
#             if outcome == 'draw':
#                 latest_wins += 0.5
#             elif outcome == 'white' and latest_is_white:
#                 latest_wins += 1
#             elif outcome == 'black' and not latest_is_white:
#                 latest_wins += 1


# """
# Evaluates the model by playing against current best (model_latest)
# Returns a win rate
# """
# def evaluate(model, num_games=20, num_workers=5):
#     manager = Manager()
#     latest_wins = manager.Value('d', 0.0)
#     total = manager.Value('d', 0.0)
#     lock = manager.Lock()

#     prev_model = network.ValueNetwork() if not os.path.exists(MODEL_LATEST) else torch.load(MODEL_LATEST, map_location="cpu")

#     workers = []
#     for _ in range(num_workers):
#         p = Process(target=worker2, args=(latest_wins, total, lock, model, prev_model), daemon=True)
#         p.start()
#         workers.append(p)

#     try:
#         while True:
#             time.sleep(1)
#             if total >= num_games:
#                 print(f"Finished evaluation against previous model. Win rate is {latest_wins / total}")
#     except KeyboardInterrupt:
#         print("Interrupted by user—shutting down.")
#         sys.exit(0)
#     finally:
#         for w in workers:
#             w.terminate()
#             w.join()
#         return latest_wins / total


# """
# Simple logic to save a model as model_latest while moving the old model_latest into checkpoints folder
# """
# def save(model):
#     if os.path.exists(MODEL_LATEST):
#         ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
#         archived = f'{CHECKPOINTS}/value_{ts}.pth'
#         os.rename(MODEL_LATEST, archived)
#     torch.save(model, MODEL_LATEST)
    
# def parse_args():
#     parser = argparse.ArgumentParser(description="Hyperparameters for self play training loop of the value network")
#     parser.add_argument(
#         "--workers",
#         type=int,
#         default=5,
#         help="Number of cpu threads being used to run parallel self play games"
#     )
#     parser.add_argument(
#         "--init_games",
#         type=int,
#         default=200,
#         help="Number of self play games for the first iteration of the training loop"
#     )
#     parser.add_argument(
#         "--ceil_games",
#         type=int,
#         default=5000,
#         help="Maximum number of games in a single self play training loop"
#     )
#     parser.add_argument(
#         "--init_policy_freedom",
#         type=int,
#         default=3,
#         help="A hyperparameter that controls how strongly the policy prefers piece captures. 0 meaning highest piece capture is always preferred 9 meaning pure random policy"
#     )
#     parser.add_argument(
#         "--init_simulations",
#         type=int,
#         default=400,
#         help="Controls the amount of simulations the mcts will go through before deciding a move in the inital training run. Gets updated as games progress"
#     )
#     parser.add_argument(
#         "--ceil_simulations",
#         type=int,
#         default=1600,
#         help="Maximum number of simulations per MCTS call in a training loop"
#     )
#     parser.add_argument(
#         "--floor_exploration_param",
#         type=int,
#         default=0.8,
#         help="Lowest allowed exploration parameter during training"
#     )
#     parser.add_argument(
#         "--draw_threshold",
#         type=int,
#         default=0.8,
#         help="Maximum percentage of games out of a training run where draws are acceptable"
#     )
#     parser.add_argument(
#         "--target_win_rate",
#         type=float,
#         default=0.55,
#         help="Target win rate against previous interation of value net chess bot"
#     )
#     return parser.parse_args()


# if __name__ == "__main__":
#     def auto_c(sims):
#         if sims < 600:
#             return 1.0
#         elif sims < 1000:
#             return 1.4
#         else:
#             return 1.8
        
#     args = parse_args()
#     num_games = args.init_games
#     simulations = args.init_simulations
#     policy_freedom = args.init_policy_freedom
#     c = auto_c(simulations)

#     loss_hist = []

#     while True:
#         states, results, stats = generate_dataset(num_games, simulations, c, policy_freedom, args.workers)
#         model, loss = train_and_eval(states, results)

#         draw_rate = stats['draws'] / stats['total']
#         win_rate = evaluate(model, 2, args.workers)

#         #too many draws = increase simulations
#         if draw_rate > args.draw_threshold and simulations < args.ceil_simulations:
#             simulations = int(min(args.ceil_simulations, simulations * 1.2))
#             c = auto_c(simulations)
#             print("[Autotune] increasing sims to reduce number of draws. sims =", simulations)

#         #not improving in performance = increase dataset size
#         elif win_rate < args.target_wins_rate and num_games < args.ceil_games:
#             num_games = (int(min(args.ceil_games, num_games * 1.25)))
#             print("[Autotune] increasing dataset size because model is not improving. num_games =", num_games)

#         #winning and loss is falling = more exploitation (lower c value)
#         elif win_rate >= args.target_win_rate and len(loss_hist) > 0 and loss < loss_hist[-1] and c > args.floor_exploration_param:
#             c = max(args.floor_exploration_param, c * 0.9)
#             print("[Autotune] reducing exploration constant because model is improving. c =", c)

#         #loss worsened twice in a row = early stop
#         elif len(loss_hist) > 1 and loss > loss_hist[-1] > loss_hist[-2]:
#             print("[Autotune] loss rose twice. Training loop is exiting")
#             break

#         loss_hist.append(loss)
#         save(model)



    

