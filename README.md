# GrietEvents

**GrietEvents** is a comprehensive event management platform designed for event organizers to manage, track, and communicate with participants. It allows event organizers to create and manage events efficiently, track participants, handle registrations, verify participants (including faculty and students), and much more. With dynamic QR generation, real-time updates, and automated mailing, GrietEvents streamlines event management and ensures seamless communication between organizers, participants, and administrators.

---
![image](https://github.com/user-attachments/assets/52eefbe0-5654-45a6-8ae9-a3b1e54225e4)

## Key Features
![image](https://github.com/user-attachments/assets/04fc9d84-36db-4f26-aa53-ff475477c312)

### Event Dashboard
- Event organizers get a comprehensive **dashboard** to manage their events, including:
  - **Event details**: View, update, or modify event information.
  - **Annoucements**: Send notifications to participants about event-related updates.
  - **Participants**: See a list of registered participants, including their details.
  - **Transactions**: Track financial transactions related to the event.
  
### Verification System
- Organizers and faculty members are verified to ensure only authorized people can manage and participate in events.
### Dynamic QR Generation for Payments
- **Dynamic QR Generation**: For participants, the platform generates unique dynamic QR codes for event payment. These QR codes can be scanned and pay required (Already filled) amount and need to enter Transaction numnber,which is sent for approval by admin.
![image](https://github.com/user-attachments/assets/5d6a8980-4def-4437-829c-160458fd93a1)

### Automated Mailing
- Automatic email notifications are sent for various purposes:
  - **Event Updates**: Participants receive updates on event details, schedules, and announcements.
  - **Registration Confirmation**: Participants get a confirmation email once they successfully register.
  - **Event-related Communications**: All necessary event-related communications are sent via email automatically.

### Registration & Approval
- **Self-Registration**: Students can register for events independently.
- **Admin Approval**: All participant registrations (including students and organizers) are subject to admin approval. Only verified participants are allowed to join.

### MongoDB Integration
- The application uses **MongoDB** as the backend database for storing event details, participant registrations, transactions, and user information. MongoDB’s flexibility ensures scalability and easy querying of data for efficient event management.

---

## Tech Stack

- **Frontend:**
  - HTML, CSS, JavaScript (for a dynamic and interactive UI)
- **Backend:**
  - Flask (for API Routing and Complete Logic)
- **Database:**
  - MongoDB (for storing event data, participant information, and transactions)
- **Authentication:**
  - JWT (JSON Web Token) for secure user authentication and authorization
- **Mailing Service:**
  - Gmail API ( For Sending Emails Automatically for Event Registration Confirmation
 and Event related updates.)  
---

## Features in Detail

### 1. **Event Registration and Management**
   - Organizers can **register** events with specific details such as event name, date, description, etc.
   - Event organizers can **update** the event details at any time.
   - Organizers can **announce** updates or important messages to all registered participants.
   - Event registration status (approved, pending, or denied) is clearly visible to both admins and participants.
![image](https://github.com/user-attachments/assets/a2877721-f8ec-447c-9e6c-39274ec6f0e8)

### 2. **Dynamic QR Code Generation**
   - For event verification, each participant receives a **dynamic QR code**.
   - The QR code can be scanned during the event for quick verification by the admin or organizers.
   - QR codes can be sent to the participants through emails and updated automatically if required.

### 3. **Automatic Email Notifications**
   - **Confirmation emails** are sent to participants upon successful registration.
   - **Event updates** (time changes, announcements) are automatically sent to all participants.
   - **Verification emails** are sent to admins or organizers when a participant's registration needs approval.

### 4. **Verification Process**
   - Both **event organizers** and **faculty members** go through a verification process to ensure only authorized people are handling or participating in events.
   - The admin manages the approval or rejection of these verifications.

### 5. **Admin Dashboard**
   - Admins have a central control panel to monitor and manage events and registrations.
   - They can **approve or reject participants**, **verify event organizers** and **faculty**, and **track transactions**.
   - Admins can also manage event announcements, ensuring participants receive up-to-date information.

### 6. **Participants’ Dashboard**
   - Participants can view event details, announcements, and their registration status.
   - They can track their **transaction status**, such as payment confirmation, and interact with organizers.
   - Participants also have the option to **update** their details and check their QR code for event verification.

---

## Installation

### Prerequisites

Before you begin, ensure you have the following installed:
- **MongoDB** (local or remote database)
- **Flask** ( Complete Logic)
