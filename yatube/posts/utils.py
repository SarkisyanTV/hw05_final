from .models import Post, Group, Comment, Follow


def create_post(text, pub_date, author, group, image=None):
    """Create a post"""

    return Post.objects.create(text=text, pub_date=pub_date, author=author, group=group, image=image)


def create_group(title, slug, description):
    """Create a group"""

    return Group.objects.create(title=title, slug=slug, description=description)

def create_follow(user, author):
    """Create a follow"""

    return Follow.objects.create(user=user, author=author)


def create_comment(post, author, text, created):
    """Create a comment"""

    return Comment.objects.create(post=post, author=author, text=text, created=created)