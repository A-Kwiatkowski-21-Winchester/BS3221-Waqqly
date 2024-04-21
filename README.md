# Deployment
This repository is connected to the corresponding Azure `ak-waqqly` web app, and will deploy automatically upon any change being pushed to the `main` branch.
Other branches such as `dev` can be used for development without the public-facing deployment being affected.


# Build and Test
## Virtual Environment Setup
It is recommended to run the following in a virtual environment. To create a virtual environment, you can use the following command:
```cmd
py -m venv .venv
```
after which, you can navigate into the venv by using:
```cmd
.venv\scripts\activate
```
### Requirements installation
If this is an initial setup, use the following command inside the venv to acquire dependencies:
```cmd
pip install -r requirements.txt
```
## Running
Once you are navigated into the venv, you can simply activate the server using:
```
flask run
```
After which you can navigate to your application at `http://localhost:5000`.
