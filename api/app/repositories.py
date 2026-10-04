"""Akses data untuk endpoint feed.

Kalau kamu perlu mengubah cara data diambil, ini file yang tepat.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Comment, Post


def list_posts(session: Session, limit: int) -> list[dict]:
    """Ambil `limit` post terbaru, lengkap dengan nama penulis dan jumlah komentar."""
    posts = (
        session.execute(select(Post).order_by(Post.created_at.desc()).limit(limit))
        .scalars()
        .all()
    )

    feed = []
    for post in posts:
        # Kita nggak memuat seluruh baris komentar cuma buat ngitung jumlahnya.
        # Lebih hemat memori daripada len(post.comments), dan hasilnya sama.
        comment_count = session.execute(
            select(func.count())
            .select_from(Comment)
            .where(Comment.post_id == post.id)
        ).scalar_one()

        feed.append(
            {
                "id": post.id,
                "title": post.title,
                "author": post.author.name,
                "comment_count": comment_count,
            }
        )

    return feed
