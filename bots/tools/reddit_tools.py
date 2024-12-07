def view_subreddit_posts(subreddit_name, limit=10, sort='hot'):
    """
    View posts from a specified subreddit.

    Use when you need to retrieve and display posts from a specific subreddit.

    Parameters:
    - subreddit_name (str): Name of the subreddit without the 'r/' prefix
    - limit (int): Maximum number of posts to retrieve (default: 10)
    - sort (str): Sort method ('hot', 'new', 'top', 'rising') (default: 'hot')

    Returns:
    A formatted string containing post information or an error message.
    """
    try:
        from datetime import datetime
        reddit, error = _get_reddit_instance()
        if error:
            return error
        subreddit = reddit.subreddit(subreddit_name)
        if sort == 'hot':
            posts = subreddit.hot(limit=limit)
        elif sort == 'new':
            posts = subreddit.new(limit=limit)
        elif sort == 'top':
            posts = subreddit.top(limit=limit)
        elif sort == 'rising':
            posts = subreddit.rising(limit=limit)
        else:
            return (
                f"Error: Invalid sort method '{sort}'. Use 'hot', 'new', 'top', or 'rising'."
                )
        formatted_posts = []
        for post in posts:
            timestamp = datetime.fromtimestamp(post.created_utc).strftime(
                '%Y-%m-%d %H:%M:%S')
            formatted_posts.append(
                f"""Title: {post.title}
Author: u/{post.author}
Posted: {timestamp}
Score: {post.score}
URL: {post.url}
ID: {post.id}
{'-' * 50}"""
                )
        if not formatted_posts:
            return f'No posts found in r/{subreddit_name}'
        return f'Posts from r/{subreddit_name}:\n\n' + '\n\n'.join(
            formatted_posts)
    except ImportError:
        return (
            "Error: PRAW is not installed. Please install it using 'pip install praw'"
            )
    except Exception as e:
        return f'Error: {str(e)}'


def view_post_comments(post_id, limit=10, sort='top'):
    """
    View comments from a specific Reddit post.

    Use when you need to retrieve and display comments from a Reddit post.

    Parameters:
    - post_id (str): The ID of the Reddit post
    - limit (int): Maximum number of top-level comments to retrieve (default: 10)
    - sort (str): Sort method ('top', 'new', 'controversial', 'old') (default: 'top')

    Returns:
    A formatted string containing comment information or an error message.
    """
    try:
        from datetime import datetime
        reddit, error = _get_reddit_instance()
        if error:
            return error
        submission = reddit.submission(id=post_id)
        submission.comments.replace_more(limit=0)
        if sort == 'top':
            submission.comment_sort = 'top'
        elif sort == 'new':
            submission.comment_sort = 'new'
        elif sort == 'controversial':
            submission.comment_sort = 'controversial'
        elif sort == 'old':
            submission.comment_sort = 'old'
        else:
            return (
                f"Error: Invalid sort method '{sort}'. Use 'top', 'new', 'controversial', or 'old'."
                )
        formatted_comments = []
        for comment in submission.comments[:limit]:
            timestamp = datetime.fromtimestamp(comment.created_utc).strftime(
                '%Y-%m-%d %H:%M:%S')
            formatted_comments.append(
                f"""Author: u/{comment.author}
Posted: {timestamp}
Score: {comment.score}
Content: {comment.body}
ID: {comment.id}
{'-' * 50}"""
                )
        if not formatted_comments:
            return f'No comments found for post ID: {post_id}'
        header = f"Comments for post: {submission.title}\n{'=' * 50}\n\n"
        return header + '\n\n'.join(formatted_comments)
    except ImportError:
        return (
            "Error: PRAW is not installed. Please install it using 'pip install praw'"
            )
    except Exception as e:
        return f'Error: {str(e)}'


def post_comment(post_id, comment_text, reply_to_comment_id=None):
    """
    Post a comment on a Reddit post or reply to an existing comment.

    Use when you need to post a new comment on a Reddit post or reply to another comment.

    Parameters:
    - post_id (str): The ID of the Reddit post
    - comment_text (str): The text content of your comment
    - reply_to_comment_id (str, optional): ID of the comment to reply to. If None, comments on the main post.

    Returns:
    A string confirming the comment was posted or an error message.
    """
    try:
        reddit, error = _get_reddit_instance(need_auth=True)
        if error:
            return error
        if not reddit.user.me():
            return 'Error: Failed to authenticate with Reddit'
        submission = reddit.submission(id=post_id)
        if reply_to_comment_id:
            comment = reddit.comment(id=reply_to_comment_id)
            new_comment = comment.reply(comment_text)
            return f"""Successfully replied to comment {reply_to_comment_id}
New comment ID: {new_comment.id}
View at: {new_comment.permalink}"""
        else:
            new_comment = submission.reply(comment_text)
            return f"""Successfully commented on post {post_id}
Comment ID: {new_comment.id}
View at: {new_comment.permalink}"""
    except ImportError:
        return (
            "Error: PRAW is not installed. Please install it using 'pip install praw'"
            )
    except Exception as e:
        return f'Error: {str(e)}'


def _get_reddit_instance(need_auth=False):
    """
    Internal helper function to get an authenticated Reddit instance.
    
    Parameters:
    - need_auth (bool): If True, includes username/password for authenticated actions
    
    Returns:
    tuple: (reddit_instance, error_message)
    """
    import os
    import praw
    try:
        client_id = os.getenv('REDDIT_CLIENT_ID')
        client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        user_agent = os.getenv('REDDIT_USER_AGENT',
            'python:bots.tools.reddit_tools:v1.0')
        if not (client_id and client_secret):
            return (None,
                'Error: Missing REDDIT_CLIENT_ID or REDDIT_CLIENT_SECRET environment variables'
                )
        if need_auth:
            username = os.getenv('REDDIT_USERNAME')
            password = os.getenv('REDDIT_PASSWORD')
            if not (username and password):
                return (None,
                    'Error: Missing REDDIT_USERNAME or REDDIT_PASSWORD environment variables'
                    )
            reddit = praw.Reddit(client_id=client_id, client_secret=
                client_secret, username=username, password=password,
                user_agent=user_agent)
        else:
            reddit = praw.Reddit(client_id=client_id, client_secret=
                client_secret, user_agent=user_agent)
        return reddit, None
    except Exception as e:
        return None, f'Error initializing Reddit instance: {str(e)}'
