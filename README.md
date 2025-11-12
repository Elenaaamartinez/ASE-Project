# 🃏 Battle Card Game Backend

This repository contains the project developed for the **Advanced Software Engineering (ASE Lab 2025/26)** course.  
The goal is to design and implement the **backend of a multiplayer card game** using a **microservices architecture**, following the functional requirements published for the lab.

---

## 🎯 Prototype Objective (November 16th Delivery)

The purpose of this delivery is to present the **initial structure of the project**, including:

- A proposed **microservices architecture**.  
- A working **Docker Compose** environment.  
- Executable containers with simple “Hello World” endpoints for the main services.  
- The foundation for future development and testing for the final delivery on **December 13th**.

---

## ⚙️ Planned Architecture

The system will consist of several microservices communicating through a **REST API** over HTTP(S).  
Each microservice will run in its own Docker container.  
The entire system can be started with:

```bash
docker compose up