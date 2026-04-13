"""
# 15 games as pink (you are p0, first mover)
python my_manager.py -n 15 -p0 agents/my_agent2.py -p1 agents/random_agent.py -l test.txt -r pink

# 15 games as black (you are p1, second mover)
python my_manager.py -n 15 -p0 agents/random_agent.py -p1 agents/my_agent2.py -l test.txt -r black
"""

from pathlib import Path
import importlib.util
import inspect
import time
import multiprocessing
import argparse

from oxono import Game, State
from agent import Agent

def find_agent_class(filename):
    spec = importlib.util.spec_from_file_location(Path(filename).stem, filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name, obj in inspect.getmembers(module, inspect.isclass):
        if issubclass(obj, Agent) and obj is not Agent:
            return obj
    return None

def run_agent_process(filename, player, conn):
    agent_class = find_agent_class(filename)
    agent = agent_class(player)

    conn.send("ready")

    while True:
        try:
            message = conn.recv()
            if message is None:
                break
            state, remaining_time = message
            try:
                action = agent.act(state, remaining_time)
                conn.send(("ok", action))
            except Exception as e:
                conn.send(("error", e))
        except EOFError:
            break

class AgentProcess:

    def __init__(self, agent_file, player):
        parent_conn, child_conn = multiprocessing.Pipe()
        self.conn = parent_conn
        self.player = player
        self.process = multiprocessing.Process(
            target=run_agent_process,
            args=(agent_file, player, child_conn),
            daemon=True
        )
        self.process.start()
        child_conn.close()

        if not self.conn.poll(timeout=30):
            self.kill()
            raise RuntimeError(f"Agent {player} failed to initialize in time")
        self.conn.recv()
    
    def get_action(self, state, remaining_time):
        self.conn.send((state, remaining_time))

        start = time.perf_counter()
        has_response = self.conn.poll(remaining_time)
        elapsed = time.perf_counter() - start

        if not has_response:
            self.kill()
            raise TimeoutError(f"Agent {self.player} exceeded time limit")

        status, value = self.conn.recv()
        if status == "error":
            raise RuntimeError(f"Agent {self.player} raised: {value}")

        return value, elapsed
    
    def kill(self):
        self.process.kill()
        self.process.join()
    
    def shutdown(self):
        try:
            self.conn.send(None)
        except Exception:
            pass
        self.process.join(timeout=2)
        if self.process.is_alive():
            self.kill()

class Manager:
    """
    Orchestrates one or more Oxono games between two agents.

    Each agent runs in an isolated subprocess, so crashes, infinite loops, and
    third-party libraries cannot interfere with the manager or with each other.
    Agent files are validated at construction time, so errors are caught before
    any game is launched.

    Parameters
    ----------
    agent_files : list[str]
        A list of exactly two filenames (e.g. ["my_agent.py", "random_agent.py"]).
        Each file must be located in the current working directory and contain a
        class that extends Agent.
    time_limit : int
        Total number of seconds each player has for the entire game (default: 300).
    """

    def __init__(self, agent_files, time_limit=300):
        self.agent_files = agent_files
        self.time_limit = time_limit

        for agent_file in self.agent_files:
            if find_agent_class(agent_file) is None:
                raise ValueError(f"No Agent subclass found in {agent_file}.")
    
    def play(self, log_file=None):
        """
        Run a single game and return the result.

        Parameters
        ----------
        log_file : file object, optional
            An already-open file to write moves into as they happen.
            The game header (log_N / time_limit / role) is written by the
            caller before calling play(); moves and error tokens are appended
            here in real time.

        Returns
        -------
        tuple[int, int]
            A (utility_p0, utility_p1) pair.
        """

        def log(text):
            if log_file is not None:
                log_file.write(text)
                log_file.flush()

        agent_0 = AgentProcess(self.agent_files[0], 0)
        agent_1 = AgentProcess(self.agent_files[1], 1)
        remaining_times = [self.time_limit, self.time_limit]

        state = State()
        result = None
        try:
            while not Game.is_terminal(state) and all(t > 0 for t in remaining_times):
                current = Game.to_move(state)
                agent = agent_0 if current == 0 else agent_1

                try:
                    action, elapsed = agent.get_action(state.copy(), remaining_times[current])
                    remaining_times[current] -= elapsed
                except TimeoutError:
                    log("timeout\n")
                    result = (-1, 1) if current == 0 else (1, -1)
                    break
                except RuntimeError as e:
                    print(e)
                    log("exception\n")
                    result = (-1, 1) if current == 0 else (1, -1)
                    break

                if action not in Game.actions(state):
                    log("invalid\n")
                    result = (-1, 1) if Game.to_move(state) == 0 else (1, -1)
                    break

                Game.apply(state, action)
                log(f"{action}, {remaining_times[current]}\n")

            if result is None:
                if remaining_times[0] <= 0:
                    result = (-1, 1)
                elif remaining_times[1] <= 0:
                    result = (1, -1)
                else:
                    result = Game.utility(state, 0), Game.utility(state, 1)

        finally:
            agent_0.shutdown()
            agent_1.shutdown()

        return result


def init_log(path, time_limit, role):
    """Create the log file and write the Game Logs header."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("Game Logs\n\n")



def append_stats(path, agent_files, n, role, per_game_results):
    """Append the final statistics block at the end of the log file."""
    p0, p1  = Path(agent_files[0]).name, Path(agent_files[1]).name
    wins_p0 = sum(1 for r in per_game_results if r == (1, -1))
    wins_p1 = sum(1 for r in per_game_results if r == (-1, 1))
    draws   = sum(1 for r in per_game_results if r == (0, 0))
    played  = len(per_game_results)

    with open(path, "a", encoding="utf-8") as f:
        f.write("Game Results\n")
        f.write(f"As {'Pink' if role == 'pink' else 'Black'} Player\n")
        f.write("Player\tWins\tWin Rate\n")
        f.write(f"{p0}\t{wins_p0}\t{100*wins_p0/played:.1f}%\n")
        f.write(f"{p1}\t{wins_p1}\t{100*wins_p1/played:.1f}%\n")
        f.write(f"Draws\t{draws}\t{100*draws/played:.1f}%\n")


if __name__ == "__main__":

    """
    Run one or more Oxono games from the command line and print aggregated results.

    Usage
    -----
        python manager.py [-n N] [-p0 FILE] [-p1 FILE] [-l FILE] [-t SECONDS]

    Arguments
    ---------
        -n  N           Number of games to play. Default: 1.
        -p0 FILE        Python file for player 0. Default: random_agent.py.
        -p1 FILE        Python file for player 1. Default: random_agent.py.
        -l  FILE        Path for the combined log file (e.g. logs/agent2.txt).
                        If omitted, no log is written.
        -t  SECONDS     Time limit per player per game in seconds. Default: 300.

    Examples
    --------
        # 15 games as pink, log to logs/agent2_pink.txt
        python manager.py -n 15 -p0 my_agent.py -p1 inginious_agent.py -l logs/agent2_pink.txt -r pink

        # 15 games as black, log to logs/agent2_black.txt
        python manager.py -n 15 -p0 inginious_agent.py -p1 my_agent.py -l logs/agent2_black.txt -r black
    """
    print("Manager started at " + time.strftime("%H:%M:%S"))

    DEFAULT_AGENT = "random_agent.py"

    parser = argparse.ArgumentParser(description="Run Oxono games between two agents")
    parser.add_argument("-n",  type=int, default=1,             help="Number of games to run (default: 1)")
    parser.add_argument("-p0", type=str, default=DEFAULT_AGENT, help="First player file (default: random_agent.py)")
    parser.add_argument("-p1", type=str, default=DEFAULT_AGENT, help="Second player file (default: random_agent.py)")
    parser.add_argument("-l",  type=str, default=None,          metavar="LOG_FILE", help="Combined log file path (default: no logging)")
    parser.add_argument("-t",  type=int, default=300,           help="Time limit for each player (default: 300)")
    parser.add_argument("-r",  type=str, default="pink",         choices=["pink", "black"], help="Your role: pink (p0 goes first) or black (p1 goes first). Default: pink")
    args = parser.parse_args()

    manager = Manager(agent_files=[args.p0, args.p1], time_limit=args.t)

    if args.l:
        init_log(args.l, args.t, args.r)

    per_game_results = []

    for i in range(args.n):
        if args.l:
            with open(args.l, "a", encoding="utf-8") as f:
                f.write(f"log_{i}.txt\n")
                f.write(f"{args.t}\n")
                f.write(f"{args.r}\n")
                result = manager.play(log_file=f)
                f.write("\n")
        else:
            result = manager.play()

        per_game_results.append(result)

        wins_p0 = sum(1 for r in per_game_results if r == (1, -1))
        wins_p1 = sum(1 for r in per_game_results if r == (-1, 1))
        draws   = sum(1 for r in per_game_results if r == (0, 0))
        played  = i + 1

        print(f"\n=== Results after game {played}/{args.n} === It is " + time.strftime("%H:%M:%S"))
        print(f"  {args.p0:<20} wins: {wins_p0:>4}  ({100 * wins_p0 / played:.1f}%)")
        print(f"  {args.p1:<20} wins: {wins_p1:>4}  ({100 * wins_p1 / played:.1f}%)")
        print(f"  Draws:                     {draws:>4}  ({100 * draws / played:.1f}%)")

    if args.l:
        append_stats(args.l, [args.p0, args.p1], args.n, args.r, per_game_results)
        print(f"\n  Log written → {args.l}")