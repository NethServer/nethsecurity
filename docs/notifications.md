---
title: Notifications
layout: default
parent: Design
---

# Notification system

* TOC
{:toc}

This system provides functionalities for managing notifications within the environment. Notifications can be utilized for:

* **User Interface Display:** Presenting messages directly to the user within the UI.
* **External Delivery:** Forwarding notifications to other systems, like email servers, for user notification via email.

The `notify` library in `python3-nethsec` manages notifications. Its functions are accessible through the `ns.notify` API.

Notifications are non-persistent, lost upon system reboot. They are saved in a sqlite database at `/var/spool/notify/notifications.db`.

## Available Actions

The notification library enables various actions on notifications:

* **Listing Notifications:** Retrieving a list of all existing notifications, including their "unread" (active) or "read" (not active).
* **Adding Notification:** Creating a new notification with specified content.
* **Deleting Notification:** Removing a notification from the system.
* **Marking as Read:** Setting the state of a notification to "read".
* **Marking as Unread:** Setting the state of a notification to "active".

## Hooks

* **Notification Addition Hook:** Upon adding a new notification, an execution hook triggers all scripts within the `/usr/libexec/notify/add` directory.
* **Notification Unread Hook:** When a notification is marked as unread, an execution hook triggers all scripts within the `/usr/libexec/notify/unread` directory.
* **Notification Read Hook:** When a notification is marked as read, an execution hook triggers all scripts within the `/usr/libexec/notify/read` directory.
* **Notification Delete Hook:** When a notification is deleted, an execution hook triggers all scripts within the `/usr/libexec/notify/delete` directory.

The hook executes all executable files within the hook directory. 
If the hook file name ends with .py, it is invoked with the current Python interpreter and can access the local `notification` variable. This variable may contain the entire notification in the case of an `add` action, or only the UUID.

## Notification format

The notifications are saved inside the database in a table named `notifications`.
The table has the following structure:

- **id:** INTEGER type column, serves as the primary key for the table.
- **level:** INTEGER type column, represents the importance level of the notification. It has a default value of 1.
  Valid values are: 0 (no level), 1 (low), 2 (medium), and 3 (high).
- **title:** TEXT type column, stores the main title of the notification. It is a required field and cannot be NULL.
  The title should identify the notification purpose, and should be something like 'os_update', 'disk_alert', etc.
- **payload:** TEXT type column, stores optional data specific to the notification. It should contain data in JSON string format.
  It has a default value of an empty string. The field is mapped to a dictionary when read using the Python library.
- **timestamp:** INTEGER type column, stores the time the notification was generated. It has a default value of the current Unix timestamp.
- **active:** INTEGER type column, represents the state of the notification. It has a default value of 1, indicating that the notification is active.
  The field value is mapped to a boolean when read using the Python library.

The level is inspired by syslog levels, and the title is used to identify the notification purpose. The payload is used to store additional data, and the timestamp is used to store the time the notification was generated.
Valid levels are:
- `0`: DEBUG
- `1`: INFO
- `2`: NOTICE
- `3`: WARNING
- `4`: ERR
- `5`: CRIT
- `6`: ALERT
- `7`: EMERG
