# Open-Meteo Weather Analytics

An end-to-end data analytics project that collects weather data from the Open-Meteo API, stores it in Google BigQuery, and transforms it into an interactive dashboard using Data Studio.

The project demonstrates a complete analytics workflow, from API data collection and cloud data storage to analysis and data visualization.

<img src="https://github.com/MaksymYakushev/data-studio-open-meteo/blob/main/images/project-preview/data-studio-preview.gif" width="900" height="650">

🔗 public data studio project: [click here](https://datastudio.google.com/reporting/a2cb3a0e-8e57-415d-84cd-73e11c1bd031) 

## Project Overview

The goal of this project is to build a weather analytics solution that makes historical and current weather conditions easier to explore and analyze over time.

The pipeline focuses on Prague, Czech Republic and combines automated data collection, cloud data warehousing, analytical transformations, and interactive reporting.


## Project Architecture

The following diagram illustrates the overall data architecture, from the external API to the final dashboard.

```mermaid
flowchart LR
    A["Open-Meteo API"] --> B["Python Data Collection"]
    B --> C["Data Processing<br/>with Pandas"]
    C --> D[("Google BigQuery")]
    D --> E["SQL Analysis<br/>& Transformations"]
    E --> F["Data Studio"]
    F --> G["Interactive<br/>Weather Dashboard"]

    classDef source fill:#e0f2fe,stroke:#0284c7,color:#0f172a
    classDef processing fill:#fef3c7,stroke:#d97706,color:#0f172a
    classDef warehouse fill:#dbeafe,stroke:#2563eb,color:#0f172a
    classDef visualization fill:#dcfce7,stroke:#16a34a,color:#0f172a

    class A source
    class B,C,E processing
    class D warehouse
    class F,G visualization
```

## Pipeline Stages

The pipeline is designed to run automatically whenever my laptop starts, keeping the weather dataset up to date without requiring any manual intervention.

**1. Automatic Execution:** When my laptop starts, the configured startup process triggers the Python data collection script.   
**2. Data Extraction:** The script retrieves the latest available weather data for Prague from the Open-Meteo API.   
**3. Data Processing:** Python and Pandas process the API response and prepare the data for storage.  
**4. BigQuery Update:** The processed weather data is uploaded to Google BigQuery, updating the dataset used for analysis.  
**5. Dashboard Refresh:** Data Studio retrieves the updated data from BigQuery and refreshes the dashboard according to its data freshness and refresh settings.

## Data Analytics Dashboard

The Data Studio dashboard provides an interactive overview of weather conditions in Prague. The dashboard is connected to Google BigQuery, allowing it to reflect updates to the underlying dataset as its data freshness and refresh settings permit. This keeps the visualizations aligned with the latest successfully loaded data without requiring manual data uploads or rebuilding the reports.

Interactive charts and filters make it easier to explore the data, investigate specific periods, and understand how weather conditions evolve over time.

The dashboard serves as the final layer of the pipeline, turning automatically collected and centrally stored data into an accessible analytics interface.

## Tools & Techniques

- **Python:** Automating API requests and orchestrating data collection.
- **Open-Meteo API:** Retrieving weather data for Prague.
- **Pandas:** Structuring and preparing data for analysis.
- **Google BigQuery:** Storing weather records in a scalable cloud data warehouse.
- **SQL:** Querying and analyzing weather data for reporting.
- **Data Studio:** Building interactive dashboards and visualizing weather trends.
- **Startup Automation:** Triggering the data collection process when the laptop starts.
- **Data Pipeline Integration:** Connecting data extraction, processing, storage, and visualization into a single workflow.
- **Git & GitHub:** Managing source code and documenting the project.

## Additional Useful Links

public data studio project: [click here](https://datastudio.google.com/reporting/a2cb3a0e-8e57-415d-84cd-73e11c1bd031)   
.pdf project: [click here](./dashboard/data-studio-open-meteo.pdf)   
.py fetch script: [click here](./src/fetch_actual_weather.py)
