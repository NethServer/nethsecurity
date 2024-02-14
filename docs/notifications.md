---
layout: default
title: Notifications
nav_order: 55
---

# Notification system

* TOC
{:toc}

This system provides functionalities for managing notifications within the environment. Notifications can be utilized for:

* **User Interface Display:** Presenting messages directly to the user within the UI.
* **External Delivery:** Forwarding notifications to other systems, like email servers, for user notification via email.

The `notify` library in `python3-nethsec` manages notifications. Its functions are accessible through the `ns.notify` API.

Notifications are non-persistent, lost upon system reboot. However, they are saved in `/var/spool/notify` within two subdirectories:
  * `active`: For unread notifications, stored as individual JSON files for efficient access and manipulation.
  * `archived`: For read notifications, also stored as individual JSON files for historical reference and potential retrieval.

## Available Actions

The notification library enables various actions on notifications:

* **Listing Notifications:** Retrieving a list of all existing notifications, including their "active" or "read" state.
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

The provided JSON format describes a notification with the following structure:

**Required Fields:**

* **priority:** (integer, 1-3) - Indicates the importance level of the notification. 1 represents low, 2 medium, and 3 high.
* **title:** (string) - The main title of the notification displayed to the user; it should identify the notification purpose.
* **uuid:** (string) - A unique identifier for the notification, typically in the format of UUID v4.

**Optional Fields:**

* **message:** (string) - Additional details or explanations about the notification.
* **payload:** (object) - Contains optional data specific to the notification. The structure and meaning of this data will depend on your application.
* **timestamp:** (integer) - Time the notification was generated, represented as the number of seconds since January 1, 1970, 00:00:00 UTC (Unix timestamp).

**Overall Structure:**

The entire notification information is represented as a single JSON object. Every field within the object is a key-value pair, where the key identifies the information and the value holds the corresponding data.

**Example:**

```json
{
  "priority": 2,
  "title": "os_update",
  "message": "OS update available: 0.0.2",
  "payload": {
    "current": "0.0.1",
    "update": "0.0.2",
    "package": "ns-ui"
  },
  "timestamp": 1660594398,
  "uuid": "850e84d1-177b-4475-823e-08a23b49fa60"
}
```

**Key Points:**

* This format provides a basic structure for managing notifications. You can adapt it to your specific needs by adding or modifying fields inside the `payload`.
* Ensure consistency and clarity by documenting any changes you make.
* Consider data security, especially when using personal information in the payload.
