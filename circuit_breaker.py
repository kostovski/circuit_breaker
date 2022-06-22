from datetime import datetime
import logging
import random
from time import sleep


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s,%(msecs)d %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)

class CircuitBreaker:
    
    def __init__(self, http_client, error_threshold, time_window):
        self.http_client = http_client
        self.error_threshold = error_threshold
        self.time_window = time_window

        # Configure states
        self.open = "open"
        self.closed = "closed"
        self.half_open = "half_open"

        # By Default state is always closed
        self.state = self.closed

        # Time when last attempt was made
        self.last_attempt = None

        # Count of failed requests
        self.failed_attempt_count = 0

    def update_last_attampt(self):
        # Set update time
        self.last_attempt = datetime.utcnow().timestamp()

    def set_state(self, state):
        # Change state
        previous_state = self.state
        self.state = state
        if self.state == "open":
            # Log error if the state is changing to open
            logging.error(f"Changed state from {previous_state} to {self.state}")
        elif self.state == "half_open":
            # Log warning if the state is changing to half_open
            logging.warning(f"Changed state from {previous_state} to {self.state}")
        else:
            # Log info if the state is changing to closed
            logging.info(f"Changed state from {previous_state} to {self.state}")

    def closed_state(self, http_client):

        # Update time of the last attempt
        self.update_last_attampt()

        # Execute if current state is closed
        if http_client['status_code'] == 200:
            logging.info("Successful Request")
            self.failed_attempt_count = 0
        else:
            logging.error("Failed Request")
            self.failed_attempt_count += 1
            logging.warning(f"Current error count is: {self.failed_attempt_count}, threshold is {self.error_threshold}")

            # If the error count is bigger then threshold then change state
            if self.failed_attempt_count >= self.error_threshold:
                self.set_state(self.open)
        
        

    def open_state(self, http_client):
        # Execute if current state is open
        current_time = datetime.utcnow().timestamp()

        # Handle to cool off period
        if self.last_attempt + self.time_window >= current_time:
            logging.warning(f"Retry after {self.last_attempt + self.time_window - current_time} secs")
            sleep(self.last_attempt + self.time_window - current_time)

        # Set the state to half_open after the delay
        self.set_state(self.half_open)

        # Update time of the last attempt
        self.update_last_attampt()

        # If successful request change the state to closed and reset the failed_attempt_count
        if http_client['status_code'] == 200:
            logging.info("Successful Request")
            self.set_state(self.closed)
            self.failed_attempt_count = 0
            logging.info("Reseting threshold to 0")
        else:
            # if the request is still failing then change the state to open again
            logging.warning("Failed Request")
            self.failed_attempt_count += 1
            logging.warning(f"Current error count is: {self.failed_attempt_count}, threshold is {self.error_threshold}")
            self.set_state(self.open)


if __name__ == "__main__":

    # Simulate random requests
    def stub_client():
        r = random.randint(0, 1)
        if r == 0:
            return {
                "state": "Success",
                "status_code": 200
            }
        return {
                "state": "Failure",
                "status_code": 500
            }
    # Create object from the Class
    breaker = CircuitBreaker(stub_client, 3, 30)
    
    # Handle the random requests
    while True:
        stub = stub_client()

        if breaker.state == "closed":
            breaker.closed_state(stub)
            sleep(1)
        else:
            breaker.open_state(stub)
            sleep(1)
 