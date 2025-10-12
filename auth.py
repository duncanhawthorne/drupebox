import dropbox


def dropbox_authorize(app_key):
    """Guides the user through the Dropbox authorization process.

    Args:
        app_key: The Dropbox application key.

    Returns:
        The refresh token obtained after successful authorization.
    """
    flow = dropbox.DropboxOAuth2FlowNoRedirect(
        app_key, use_pkce=True, token_access_type="offline"
    )
    authorize_url = flow.start()
    print("1. Go to: " + authorize_url)
    print('2. Click "Allow" (you might have to log in first)')
    print("3. Copy the authorization code.")
    code = input("Enter the authorization code here: ").strip()
    return flow.finish(code).refresh_token
