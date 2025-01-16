import random
import string

from locust import HttpUser, between, task


class PastebinUser(HttpUser):
    # Wait between 1 and 5 seconds between tasks
    wait_time = between(1, 2)

    def on_start(self):
        """Initialize user's session data."""
        self.paste_ids = []  # Store created paste IDs
        self.sample_content = [
            "print('Hello, World!')",
            "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
            "SELECT * FROM users WHERE age > 18;",
            "body { background-color: #f0f0f0; }",
            "console.log('JavaScript test');",
        ]
        self.languages = [
            "python",
            "javascript",
            "css",
            "sql",
            "bash",
            "yaml",
            "json",
            "plaintext",
        ]

    def generate_random_string(self, length=100):
        """Generate random content for pastes."""
        return "".join(
            random.choices(
                string.ascii_letters + string.digits + string.punctuation + " \n",
                k=length,
            )
        )

    @task(3)  # Higher weight for viewing home page
    def view_home_page(self):
        """Test accessing the home page."""
        with self.client.get("/", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Home page failed with status {response.status_code}")

    @task(2)
    def create_paste(self):
        """Test creating a new paste."""
        content = random.choice(self.sample_content)
        if random.random() < 0.3:  # 30% chance of longer content
            content += "\n" + self.generate_random_string(500)

        data = {
            "content": content,
            "title": f"Test Paste {random.randint(1, 1000)}",
            "language": random.choice(self.languages),
        }

        # Sometimes add a password
        if random.random() < 0.2:  # 20% chance of password protection
            data["password"] = "test123"

        with self.client.post("/paste", data=data, catch_response=True) as response:
            if response.status_code == 302:  # Successful redirect
                # Extract paste ID from redirect URL
                paste_id = response.headers["Location"].split("/")[-1]
                self.paste_ids.append(paste_id)
            else:
                response.failure(
                    f"Paste creation failed with status {response.status_code}"
                )

    @task(4)  # Higher weight for viewing pastes
    def view_paste(self):
        """Test viewing existing pastes."""
        if self.paste_ids:
            # View a previously created paste
            paste_id = random.choice(self.paste_ids)
            with self.client.get(f"/paste/{paste_id}", catch_response=True) as response:
                if response.status_code != 200:
                    response.failure(
                        f"Paste view failed with status {response.status_code}"
                    )
        else:
            # If no pastes created yet, view home page instead
            self.view_home_page()

    @task(1)
    def view_nonexistent_paste(self):
        """Test viewing a non-existent paste."""
        fake_id = "".join(random.choices(string.ascii_letters + string.digits, k=8))
        with self.client.get(f"/paste/{fake_id}", catch_response=True) as response:
            if response.status_code not in [
                302,
                404,
            ]:  # Both redirect and 404 are acceptable
                response.failure(
                    f"Unexpected status code {response.status_code} for non-existent paste"
                )


class PastebinAdminUser(PastebinUser):
    """Simulates admin users with different behavior patterns."""

    @task(2)
    def create_large_paste(self):
        """Test creating pastes with large content."""
        data = {
            "content": self.generate_random_string(5000),  # 5KB content
            "title": f"Large Test Paste {random.randint(1, 1000)}",
            "language": random.choice(self.languages),
        }

        with self.client.post("/paste", data=data, catch_response=True) as response:
            if response.status_code == 302:
                paste_id = response.headers["Location"].split("/")[-1]
                self.paste_ids.append(paste_id)
            else:
                response.failure(
                    f"Large paste creation failed with status {response.status_code}"
                )


if __name__ == "__main__":
    # This section is for local testing without the Locust UI
    from locust import run_single_user

    # Create an instance of PastebinUser
    user = PastebinUser(None)
    # Run the user instance
    run_single_user(user)
