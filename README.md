# PULSE

**PULSE** is a lightweight B2B application designed to help gyms monitor member attendance and identify early signs of dropout risk.

The system focuses on **engagement and retention**, providing simple, explainable indicators that allow gym managers and instructors to act before members abandon their training routine.

---

## 🎯 Purpose

Gym member dropout is one of the main challenges faced by fitness centers.  
PULSE addresses this problem by transforming **attendance data** into **actionable insights**.

PULSE does **not** prescribe workouts, provide health diagnoses, or replace professional supervision.

---

## 🚀 Key Features

- Weekly attendance tracking  
- Detection of frequency decline  
- Dropout risk score (0–100)  
- Visual alerts for high-risk members  
- Simple CSV-based data input  
- Explainable and rule-based logic  

---

## 📊 How It Works

PULSE analyzes attendance patterns using simple, transparent rules:

- Average weekly attendance  
- Recent drop in frequency  
- Consecutive absences  
- Irregular attendance patterns  

These factors are combined into a **Dropout Risk Score**, allowing gym staff to prioritize follow-up actions.

---

## 🧠 Dropout Risk Score

| Score Range | Interpretation |
|------------|----------------|
| 0–30       | Low risk       |
| 31–60      | Moderate risk  |
| 61–100     | High risk      |

The score is designed to be **interpretable**, not predictive medicine.

---

## 📂 Data Input

PULSE currently accepts a CSV file with the following structure:

```csv
member_id,date
001,2025-01-02
001,2025-01-05
002,2025-01-03

