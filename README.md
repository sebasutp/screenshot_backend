# Screenshot Capture Backend in FastAPI

Do you find sometimes the need to share screenshots with friends? This project
might be for you. You might also want to check the Chrome plugin in
[this repo](https://github.com/sebasutp/screenshot-capture) to capture
screenshots from Chrome and add them to the backend.

## Requirements

* Make sure to use Python3.10 or newer.

## Want to test this project locally project?

1. Fork/Clone

2. Create and activate a virtual environment:

    ```sh
    $ python3 -m venv venv && source venv/bin/activate
    ```

3. Install the requirements:

    ```sh
    (venv)$ pip install -r requirements.txt
    ```

4. Create a `.env` file in the root folder and add the following configuration:

    ```sh
    JWT_SECRET="some random secret key"
    JWT_ALGORITHM="HS256"
    DB_URL="sqlite:///database.db"
    TOKEN_TIMEOUT=30
    ```

5. Run the app:

    ```sh
    (venv)$ python main.py
    ```

6. Test at [http://localhost:8081/docs](http://localhost:8081/docs)

**Note**: the random secret `JWT_SECRET` can be generated for example 
using a command like this one:

```sh
openssl rand -hex 32
```

Feel free to change any of the configuration variables in `.env` to
match your needs.
