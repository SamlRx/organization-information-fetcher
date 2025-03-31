# Organization Information Fetcher

## Overview

The Organization Information Fetcher is a Python-based application designed to gather, clean, and store detailed information about various organizations. It uses web crawling and structured data extraction techniques to compile comprehensive company profiles.

## Features

- **Web Crawling**: Automatically searches the web for company information.
- **Data Cleaning**: Ensures the gathered data is structured and complete.
- **Data Storage**: Saves the cleaned data into CSV files for further analysis.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/SamlRx/organization_information_fetcher.git
    cd organization_information_fetcher
    ```

2. Install `uv` if not already installed:
    ```sh
    pip install uv
    ```

3. Create a virtual environment:
    ```sh
    uv venv
    ```

## Usage

1. Run the application:
    ```sh
    python src/organization_information_fetcher_app/main.py
    ```

2. To run tests:
    ```sh
    pytest
    ```

## Configuration

1. Create a `.env` file in the root directory of the project.
2. Add the following environment variables to the `.env` file:
    ```sh
    # .env
    MISTRAL_API_KEY=YOUR_MISTRAL_API_KEY
    ```

## Contributing

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Create a new Pull Request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contact

For any inquiries, please contact [SamlRx](https://github.com/SamlRx).
