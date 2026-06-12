# 01. Project Overview

## Problem Statement

Electric Vehicle (EV) owners face a complex decision every time they plug in their vehicles. They must balance three competing objectives:

1.  **Minimize Electricity Cost:** Electricity prices, especially with Time-of-Use (TOU) or dynamic pricing, fluctuate significantly throughout the day. Charging during peak hours can be vastly more expensive than off-peak.
2.  **Preserve Battery Health:** EV batteries degrade over time. Factors accelerating degradation include charging in extreme temperatures, charging to very high States of Charge (SoC), and frequent fast charging (high C-rates).
3.  **Ensure Readiness:** The vehicle must be charged to the target level before the user's scheduled departure time.

Most existing charging solutions are either immediate (plug and charge) or use basic timers (start at midnight), ignoring dynamic pricing and battery health entirely.

## Project Objective

The **AI-Powered Smart EV Charging Recommendation System** is designed to solve this optimization problem. It acts as an intelligent advisor that takes user inputs, environmental data, and electricity pricing to generate the mathematically optimal charging schedule.

## Key Features

*   **Linear Programming Optimization:** Uses the PuLP library and CBC solver to find the absolute minimum-cost charging schedule that guarantees the vehicle is ready by departure.
*   **Battery Degradation Modeling:** Incorporates heuristic models based on temperature (Arrhenius equation), SoC stress, and C-rate to penalize charging behaviors that harm the battery.
*   **Weather Awareness:** Adjusts charging efficiency based on ambient temperature and flags opportunities for solar charging.
*   **Cost Analysis:** Provides transparent comparisons between a "naive" (immediate) charging strategy and the optimized schedule, highlighting exact dollar and percentage savings.
*   **AI Recommendations:** Generates human-readable, actionable advice explaining *why* the schedule was chosen and how the user can improve battery longevity.

## Target Audience

*   EV owners looking to reduce home charging costs.
*   Fleet managers optimizing charging schedules for multiple vehicles.
*   Energy companies or smart-home platforms integrating intelligent load shifting.
