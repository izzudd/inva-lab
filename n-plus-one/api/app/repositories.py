"""Akses data untuk endpoint feed.

Versi solusi. Dua perubahan, di dua tempat yang berbeda:

1. Di aplikasi: relasi author dimuat sekaligus (joinedload), dan jumlah komentar
   diambil sebagai satu query agregat (GROUP BY) untuk seluruh halaman.
2. Di database: index di comments(post_id) - lihat db/init/03_index.sql.

Keduanya wajib. Mengerjakan nomor 1 saja membuat query jadi 2, tapi latency masih
~60 ms karena setiap agregat masih membaca seluruh tabel.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from .models import Comment, Post


def list_posts(session: Session, limit: int) -> list[dict]:
    """Ambil `limit` post terbaru, lengkap dengan nama penulis dan jumlah komentar."""
    posts = (
        session.execute(
            select(Post)
            .options(joinedload(Post.author))
            .order_by(Post.created_at.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )

    post_ids = [post.id for post in posts]

    # Satu query agregat untuk seluruh halaman, bukan satu query per post.
    # Kita nggak pernah butuh baris komentarnya - cuma angkanya.
    counts = dict(
        session.execute(
            select(Comment.post_id, func.count())
            .where(Comment.post_id.in_(post_ids))
            .group_by(Comment.post_id)
        ).all()
    )

    return [
        {
            "id": post.id,
            "title": post.title,
            "author": post.author.name,
            "comment_count": counts.get(post.id, 0),
        }
        for post in posts
    ]
