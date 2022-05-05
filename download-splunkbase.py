#!/usr/bin/env python3
import requests
import cgi
import argparse
from bs4 import BeautifulSoup


def get_form_details(form):
    """Returns the HTML details of a form,
    including action, method and list of form controls (inputs, etc)"""
    # get the form action (requested URL)
    action = form.attrs.get('action').lower()
    # get the form method (POST, GET, DELETE, etc)
    # if not specified, GET is the default in HTML
    method = form.attrs.get('method', 'get').lower()
    # get all form inputs
    data = {}
    for input_tag in form.find_all('input'):
        # get name attribute
        input_name = input_tag.attrs.get('name')
        # get the default value of that input tag
        input_value = input_tag.attrs.get('value', '')
        # add everything to the data object
        data[input_name] = input_value
    return action, method, data


def submit_form(session, form):
    action, method, form_data = get_form_details(form)
    if method == 'post':
        session.post(action, data=form_data)
    elif method == 'get':
        session.get(action, data=form_data)


def download(username, password, app_id, version):
    url = f'https://splunkbase.splunk.com/app/{app_id}/release/{version}/download'
    urlauth = 'https://account.splunk.com/api/v1/okta/auth'
    session = requests.session()
    # Base auth with okta, store cookies
    auth_req = session.post(
        urlauth, json={'username': username, 'password': password}).json()
    if 'status_code' in auth_req and auth_req['status_code'] != 200:
        raise ValueError('Error authenticating, response: ',
                         auth_req['message'])
    # Try requesting the download url for the release. The first request actually returns a okta intersitual page that needs to be resolved and submitted
    soup = BeautifulSoup(session.get(url).content, 'html.parser')
    # Scrape out the intersitual page and submit it
    submit_form(session, soup.find('form'))
    # The second request returns the package
    response = session.get(url)
    _, params = cgi.parse_header(response.headers.get('Content-Disposition'))
    filename = params['filename']
    with open(filename, 'wb') as f:
        f.write(response.content)
    print(f'Successfully downloaded package {filename}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('username', help='Splunkbase username')
    parser.add_argument('password', help='Splunkbase password')
    parser.add_argument('app_id', help='ID of application to download')
    parser.add_argument('version', help='Version of application to download')
    args = parser.parse_args()
    download(args.username, args.password, args.app_id, args.version)
