# Submission Data Analyst

## Setup Environment - Anaconda
conda create --name main-ds python=3.9
conda activate main-ds
pip install -r requirements.txt

## Setup Environment - Shell/Terminal
mkdir submission_data_analyst
cd submission_data_analyst
pipenv install
pipenv shell
pip install -r requirements.txt

## Run steamlit app
streamlit run dashboard.py
