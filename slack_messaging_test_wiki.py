import requests
import random
from slack_sdk import WebClient

token = ""
client = WebClient(token=token)
user_id = "victor.luong"
channel_id = "C0C9SDDE06N"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json; charset=utf-8"
}



def test_messages():
    response_send1 = client.chat_postMessage(
        channel=channel_id,
        text="First test message!"
    )
    print(response_send1["ok"])

    timestamp1 = response_send1["ts"]

    response_reply1 = client.chat_postMessage(
        channel=channel_id,
        text="First reply test message!",
        thread_ts=timestamp1
    )
    print(response_reply1["ok"])

    timestamp2 = response_reply1["ts"]

    response_update1 = client.chat_update(
        channel=channel_id,
        text=f"First edited test message for <@{user_id}>!",
        ts=timestamp1
    )
    print(response_update1["ok"])

    response_reply2 = client.chat_postMessage(
        channel=channel_id,
        text="Second reply test message!",
        thread_ts=timestamp1
    )
    print(response_reply2["ok"])

    timestamp3 = response_reply2["ts"]

    response_convos1 = client.conversations_replies(
        channel=channel_id,
        ts=timestamp1
    )

    if len(response_convos1["messages"] )> 0:
        reply_post = "Someone has replied!"
    else:
        reply_post = "Nobody has replied yet."

    response_reply3 = client.chat_postMessage(
        channel=channel_id,
        text="First reply reply test message!",
        thread_ts=timestamp3
    )
    print(response_reply3["ok"])


    response_convos2 = client.conversations_replies(
        channel=channel_id,
        ts=timestamp1
    )

    for message in response_convos2["messages"]:
        print(message["blocks"])

# def generate_frames():
#     version = "v043"
#     shot = "tst04_070"
#     job_link = "https://www.google.com"

#     for pass_type in ["char01", "prop", "env",]:
#         response = client.chat_postMessage(
#             channel=channel_id,
#             text=f"<https://www.apple.com|App> Job made for {version} {shot} {pass_type}.",
#             unfurl_links=False,
#             unfurl_media=False
#         )
        
#         job_ts = response["ts"]

#         for frame in range(1001, 1011):
#             failed = random.choices([True, False], weights=[1, 9])[0]
#             create_failed_frame_msg(job_ts, job_link, version, shot, pass_type, frame, failed)

# def create_failed_frame_msg(job_ts, job_link, version, shot, pass_type, frame, failed):
#     response = client.conversations_replies(
#         channel=channel_id,
#         ts=job_ts
#     )

#     print(f"Frame failure: {failed}")

#     if failed:
#         print(len(response["messages"]))
#         if len(response["messages"]) == 1 :
#             response_update = client.chat_update(
#                 channel=channel_id,
#                 text=f"<@{user_id}> <{job_link}|Google> Job made for {version} {shot} {pass_type} - Failed.",
#                 ts=job_ts
#             )
#             print(response_update["ok"])

#         response_reply = client.chat_postMessage(
#             channel=channel_id,
#             text=f"Failure for frame {frame}!",
#             thread_ts=job_ts
#         )

#         print(response_reply["ok"])



def generate_frames_requests():
    version = "v043"
    shot = "tst04_070"
    job_link = "https://www.google.com"

    for pass_type in ["char01", "prop", "env",]:
        response = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers=headers,
            json={
                "channel": channel_id,
                "text": (
                    f"<https://www.apple.com|App> "
                    f"Job made for {version} {shot} {pass_type}."
                ),
                "unfurl_links": False,
                "unfurl_media": False
            }
        ).json()
        
        job_ts = response["ts"]

        for frame in range(1001, 1011):
            failed = random.choices([True, False], weights=[1, 9])[0]
            create_failed_frame_msg_requests(job_ts, job_link, version, shot, pass_type, frame, failed)

def create_failed_frame_msg_requests(job_ts, job_link, version, shot, pass_type, frame, failed):
    print("Did it fail?", failed)

    if failed:
        response = requests.get(
            "https://slack.com/api/conversations.replies",
            headers=headers,
            params={
                "channel": channel_id,
                "ts": job_ts
            }
        ).json()

        if len(response["messages"]) == 1 :
            response_update = requests.post(
                "https://slack.com/api/chat.update",
                headers=headers,
                json={
                    "channel": channel_id,
                    "ts": job_ts,
                    "text": (
                        f"<@{user_id}> <{job_link}|Google> "
                        f"Job made for {version} {shot} "
                        f"{pass_type} - Failed."
                    )
                }
            ).json()

        response_reply = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers=headers,
            json={
                "channel": channel_id,
                "text": f"Failure for frame {frame}!",
                "thread_ts": job_ts
            }
        ).json()

generate_frames_requests()



"""
Flow:
Job is created.
Tasks for making frames are generated.
If frame task fails, it creates a new message for a job and either:
- Replies to it
- Edits it with the failed task information

Notes:
You wouldn't be able to get the timestamp of the initial job if they all don't know when a job will fail.

Questions:
- Currently, it seems like you can only reply to message with a given timestamp. Can you find messages without their timestamp?

Potential solutions:
Create a job message regardless of whether it has failed or not. Give the ts to all frames for potential replies. If it fails, replies will occur.
- If edits to pings actually ping the user - ping the user with an edit.

If a job message doesn't already exist that matches the same text for the shot, pass, frame and version without using ts, send it then reply to it.
Otherwise, reply to the job message. 

Learning Notes:
A reply to a reply will look just the same as replying to the main message.
Pinging someone in an edit will retroactively ping them.

Need:
channels:history
chat:write

channel_id
token -> client

"""
