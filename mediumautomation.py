import json
import requests
from datetime import datetime, timedelta
import csv


#Medium Automation Script to get a csv list of interesting users in Medium


MEDIUM = 'https://medium.com'

def clean_json_response(response):
	return json.loads(response.text.split('])}while(1);</x>')[1])


def get_user_id(username):

	print('Retrieving user id...')
	url = MEDIUM + '/@' + username + '?format=json'
	response  = requests.get(url)
	response_dict = clean_json_response(response)
	return response_dict['payload']['user']['userId']

def get_list_of_followings(user_id):

    print('Retrieving users from Followings...')
    
    next_id = False
    followings = []

    while True:

        if next_id:
            # If this is not the first page of the followings list
            url = MEDIUM + '/_/api/users/' + user_id
                  + '/following?limit=8&to=' + next_id
        else:
            # If this is the first page of the followings list
            url = MEDIUM + '/_/api/users/' + user_id + '/following'

        response = requests.get(url)
        response_dict = clean_json_response(response)
        payload = response_dict['payload']

        for user in payload['value']:
            followings.append(user['username'])

        try:
            # If the "to" key is missing, we've reached the end
            # of the list and an exception is thrown
            next_id = payload['paging']['next']['to']
        except:
            break

    return followings


def get_list_of_latest_posts_ids(usernames):

    print('Retrieving the latest posts...')

    post_ids = []

    for username in usernames:
        url = MEDIUM + '/@' + username + '/latest?format=json'
        response = requests.get(url)
        response_dict = clean_json_response(response)

        try:
            posts = response_dict['payload']['references']['Post']
        except:
            posts = []

        if posts:
            for key in posts.keys():
                post_ids.append(posts[key]['id'])

    return post_ids


def get_post_responses(posts):

    print('Retrieving the post responses...')

    responses = []

    for post in posts:
        url = MEDIUM + '/_/api/posts/' + post + '/responses'
        response = requests.get(url)
        response_dict = clean_json_response(response)
        responses += response_dict['payload']['value']

    return responses


def check_if_high_recommends(response, recommend_min):
    if response['virtuals']['recommends'] >= recommend_min:
        return True


def check_if_recent(response):
    limit_date = datetime.now() - timedelta(days=30)
    creation_epoch_time = response['createdAt'] / 1000
    creation_date = datetime.fromtimestamp(creation_epoch_time)

    if creation_date >= limit_date:
        return True


def get_user_ids_from_responses(responses, recommend_min):

    print('Retrieving user IDs from the responses...')

    user_ids = []

    for response in responses:
        recent = check_if_recent(response)
        high = check_if_high_recommends(response, recommend_min)

        if recent and high:
            user_ids.append(response['creatorId'])

    return user_ids


def get_usernames(user_ids):

    print('Retrieving usernames of interesting users...')

    usernames = []

    for user_id in user_ids:
        url = MEDIUM + '/_/api/users/' + user_id
        response = requests.get(url)
        response_dict = clean_json_response(response)
        payload = response_dict['payload']

        usernames.append(payload['value']['username'])

    return usernames


def get_interesting_users(username, recommend_min):

    print('Looking for interesting users for %s...' % username)

    user_id = get_user_id(username)

    usernames = get_list_of_followings(user_id)

    posts = get_list_of_latest_posts_ids(usernames)

    responses = get_post_responses(posts)

    users = get_user_ids_from_responses(responses, recommend_min)

    return get_usernames(users)

def list_to_csv(interesting_users_list):
    with open('recommended_users.csv', 'a') as file:
        writer = csv.writer(file)

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        interesting_users_list.insert(0, now)
        
        writer.writerow(interesting_users_list)