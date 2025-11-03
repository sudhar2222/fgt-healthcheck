<h1 align="center" style="font-size:42px;"> FortiManager Health Check Automation </h1>

<p align="center">
A Python-based automation tool that performs API-driven health checks on <b>FortiGate devices managed by FortiManager</b> — enhanced with a locally deployed <b>Phi-3 Mini LLM</b> for human-readable summaries.
</p>

---

<h2 style="font-size:30px;">🚀 Project Overview</h2>

This project runs on a **Linux environment** and uses **FortiManager’s REST API** to query managed FortiGate devices for operational and health metrics.  

Currently, it supports **retrieving BGP summary information**, with future plans to include additional health and performance checks.  

Once the raw results are fetched, they are passed to a **locally hosted LLM (Phi-3 Mini)**, which interprets and simplifies the data into an easy-to-understand report using **prompt engineering**.

---

<h2 style="font-size:30px;">🧠 Features</h2>

### ✅ Current Functionality
- Retrieve **BGP summary** information from FortiManager-managed FortiGate devices.
- Use **Phi-3 Mini (local LLM)** to interpret and summarize results.
- Provide **non-technical summaries** for better readability.

### 🔜 Planned Enhancements
- **VPN status checks**
- **Performance statistics** (CPU, memory, session counts)
- **HA (High Availability) status**
- **Routing table summaries**
- **Interface health checks**
- **Custom prompt templates** for different diagnostic contexts

---

<h2 style="font-size:30px;">🏗️ Architecture Overview</h2>




![Untitled Diagram](https://github.com/user-attachments/assets/9e5d572b-97e2-413b-a5a5-916f1dca0f56)

---

<h2 style="font-size:30px;">🧰 Tech Stack</h2>

| Component | Description |
|------------|--------------|
| **Language** | Python 3 |
| **API Framework** | FortiManager REST API |
| **LLM Model** | Phi-3 Mini (Local Deployment) |
| **Platform** | Linux |


---

<h2 style="font-size:30px;">⚙️ Setup & Usage</h2>

### 1️⃣ Clone the Repository
