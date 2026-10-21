from datetime import datetime
import os
import time


# ------------------------------------------------------------
# SHARED LOG FILE
# ------------------------------------------------------------

LOG_FILE = "flooding_log.txt"
LOCK_FILE = "flooding_log.txt.lock"

class Logger:

    def __init__(self, node_name):

        self.node_name = node_name

        # Local statistics for this node
        self.total_received = 0
        self.unique_received = 0
        self.duplicate_received = 0

        self.total_forwarded = 0
        self.total_delivered = 0

        self.failed_nodes_detected = 0
        self.probabilistic_drops = 0
        self.forward_attempts = 0

    # ========================================================
    # ACQUIRE FILE LOCK
    # ========================================================

    def acquire_file_lock(self):

        # Maximum time we will wait for the lock
        max_wait_time = 5

        start_time = time.time()

        while True:

            try:

                # "x" means:
                # create the file only if it does not exist
                self.lock_file_handle = open(
                    LOCK_FILE,
                    "x"
                )

                return True

            except FileExistsError:

                # Another node currently has the lock

                if time.time() - start_time > max_wait_time:

                    # The lock may be stale.
                    # Try to remove it.

                    try:
                        os.remove(LOCK_FILE)

                    except (FileNotFoundError, PermissionError):
                        pass

                    start_time = time.time()

                time.sleep(0.02)

            except PermissionError:

                # Windows / OneDrive may temporarily report
                # PermissionError while accessing the lock file.

                if time.time() - start_time > max_wait_time:

                    # Instead of crashing the node, we give up
                    # on the lock and allow the log write to continue.

                    return False

                time.sleep(0.05)

            except OSError:

                # Other Windows file-system issue

                if time.time() - start_time > max_wait_time:

                    return False

                time.sleep(0.05)

    # ========================================================
    # RELEASE FILE LOCK
    # ========================================================

    def release_file_lock(self):

        # Close our lock file if we successfully opened it

        try:

            if hasattr(self, "lock_file_handle"):

                self.lock_file_handle.close()

        except Exception:
            pass

        # Delete the lock file

        try:

            os.remove(LOCK_FILE)

        except (FileNotFoundError, PermissionError, OSError):

            pass

    # ========================================================
    # WRITE MESSAGE TO SHARED LOG
    # ========================================================

    def write(self, node_name, message):

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )[:-3]

        lock_acquired = False

        try:

            # Try to acquire shared lock

            lock_acquired = self.acquire_file_lock()

            # ------------------------------------------------
            # WRITE LOG
            # ------------------------------------------------

            with open(
                LOG_FILE,
                "a",
                encoding="utf-8"
            ) as file:

                file.write(
                    f"[{timestamp}] "
                    f"[Node {node_name}] "
                    f"{message}\n"
                )

                file.flush()

        except Exception as error:

            # IMPORTANT:
            # A logging problem must NEVER kill the
            # networking node.
            # Therefore we only print the error.

            print(
                f"[LOGGER WARNING] "
                f"Node {node_name}: "
                f"Could not write to log: {error}"
            )

        finally:

            # Release lock if necessary

            if lock_acquired:

                self.release_file_lock()

    # ========================================================
    # STATISTICS FUNCTIONS
    # ========================================================

    def received_packet(self):

        self.total_received += 1

    # --------------------------------------------------------

    def unique_packet(self):

        self.unique_received += 1

    # --------------------------------------------------------

    def duplicate_packet(self):

        self.duplicate_received += 1

    # --------------------------------------------------------

    def forwarded_packet(self):

        self.total_forwarded += 1

    # --------------------------------------------------------

    def delivered_packet(self):

        self.total_delivered += 1

    # --------------------------------------------------------

    def failed_node_detected(self):

        self.failed_nodes_detected += 1

    # --------------------------------------------------------

    def probabilistic_drop(self):

        self.probabilistic_drops += 1

    # --------------------------------------------------------

    def forwarding_attempt(self):

        self.forward_attempts += 1

    # ========================================================
    # PRINT LOCAL STATISTICS
    # ========================================================

    def print_statistics(self):

        print()
        print("=" * 70)

        print(
            f"LOCAL STATISTICS - NODE "
            f"{self.node_name}"
        )

        print("=" * 70)

        print(
            f"Total Packets Received      : "
            f"{self.total_received}"
        )

        print(
            f"Unique Packets Received     : "
            f"{self.unique_received}"
        )

        print(
            f"Duplicate Packets Received : "
            f"{self.duplicate_received}"
        )

        print(
            f"Packets Forwarded           : "
            f"{self.total_forwarded}"
        )

        print(
            f"Packets Delivered           : "
            f"{self.total_delivered}"
        )

        print(
            f"Failed Nodes Detected       : "
            f"{self.failed_nodes_detected}"
        )

        print(
            f"Probabilistic Drops         : "
            f"{self.probabilistic_drops}"
        )

        print(
            f"Forwarding Attempts         : "
            f"{self.forward_attempts}"
        )

        print("=" * 70)
