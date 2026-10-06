# Open-Meteo Weather Analytics

## Project Idea

This project focuses on collecting, storing, and visualizing weather data using **Open-Meteo, Google BigQuery, and Data Studio**.

The main goal is to build an analytics solution that allows users to explore weather conditions and their changes over time across different cities.

Weather data is collected from the Open-Meteo API and stored in **Google BigQuery**, where it can be queried and transformed for analytical purposes. The resulting data is then connected to **Data Studio** to create interactive dashboards and visualizations.

At the current stage, the project focuses on weather data for **Prague, Czech Republic**.

## Project Architecture

```mermaid
flowchart LR
    A[Open-Meteo API] --> B[Data Collection]
    B --> C[Google BigQuery]
    C --> D[Data Analysis & Transformation]
    D --> E[Data Studio]
    E --> F[Interactive Weather Dashboard]
```

## Current Scope

- Weather data collection from Open-Meteo
- Data storage in Google BigQuery
- Weather analytics and data transformation
- Visualization in Data Studio
- Initial focus on Prague weather data