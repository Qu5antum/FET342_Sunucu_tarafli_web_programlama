# Poll Management System

A web-based polling and survey management system built with Django.  
The platform allows users to create polls, participate in surveys, share private polls via unique links, and analyze voting results.

---

# Features

## Authentication System
- User login/logout
- Role-based access
- Group-based poll visibility

## Poll Management
- Create public or private polls
- Add poll expiration date
- Share polls using unique UUID links
- Restrict access by groups

## Question System
Supports:
- Single Choice Questions
- Multiple Choice Questions

Each poll can contain:
- Unlimited questions
- Unlimited options per question

## Voting System
- One participation per user
- Multiple choice support
- Vote cancellation support
- Validation for unanswered questions

## Poll Expiration
- Polls automatically close after deadline
- Countdown timer on poll page
- Different messages for:
  - users who voted
  - users who missed the poll

## Results System
- Real-time vote counting
- Result visualization
- Per-option statistics

---

# Technologies

## Backend
- Python
- Django
- SQLite

## Frontend
- HTML5
- CSS3
- Vanilla JavaScript

---

# Database Structure

## Main Models

### Poll
Stores poll information:
- title
- description
- visibility
- expiration date

### Question
Stores poll questions:
- text
- question type

### Option
Stores selectable answers.

### Vote
Stores user votes.

### PollParticipation
Prevents multiple submissions.

### PollShare
Stores unique private poll links.

---

# Question Types

## Single Choice
User can select only one option.

## Multiple Choice
User can select multiple options.

---

# Visibility Types

## Public
Visible to all users.

## Private
Accessible only through:
- selected groups
- shared private links

---

# Installation

## Clone Repository

```bash
git clone <repository_url>
cd project_name
```

## Create Virtual Environment

```bash
python -m venv venv
```

## Activate Environment

### Windows
```bash
venv\Scripts\activate
```
### Linux / macOS
```bash
source venv/bin/activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

## Start Server

```bash
python manage.py runserver
```