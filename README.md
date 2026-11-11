# Blog API

REST API backend for a blog application, built with FastAPI, SQLAlchemy, and PostgreSQL.

## Related projects

- Frontend: [serjstratu/blog-app](https://github.com/serjstratu/blog-app)

## Requirements

- Python 3.13 or newer
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL

## Run locally

1. Install the dependencies:

   ```bash
   uv sync
   ```

2. Create a `.env` file based on `.env.example`. Set the PostgreSQL connection string and JWT secret:

   ```env
   DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/DATABASE
   JWT_SECRET_KEY=replace-with-a-long-random-secret
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   ```

3. Make sure the database has a `users` table with `avatar` and `bio` columns. Run the SQL in `app/scripts/create_posts_table.sql` against the same PostgreSQL database, using a client such as pgAdmin or `psql`.

   The PostgreSQL role specified in `DATABASE_URL` needs `SELECT`, `INSERT`, `UPDATE`, and `DELETE` privileges on `posts`, plus `USAGE` and `SELECT` privileges on the `posts_id_seq` sequence. The posts table references the existing `users` table.

4. Start the API:

   ```bash
   uv run uvicorn main:app --reload
   ```

The API is available at `http://127.0.0.1:8000`. Interactive Swagger documentation is at `http://127.0.0.1:8000/docs`.

## API

API routes use the `/api` prefix.

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/login` | Log in with a username or email and receive a JWT access token |

Example request body:

```json
{
  "login": "user@example.com",
  "password": "your-password"
}
```

For protected routes, include the token in the request header:

```http
Authorization: Bearer <access_token>
```

### Users

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/users/` | List users |
| GET | `/api/users/{id}` | Get a user |
| PATCH | `/api/users/{id}` | Update your own `name`, `bio`, or `phone` |
| POST | `/api/users/{id}/avatar` | Upload your own avatar |
| DELETE | `/api/users/{id}/avatar` | Delete your own avatar |

To upload an avatar, send `multipart/form-data` with a `file` field. JPEG, PNG, and WebP images up to 5 MB are supported. Files are stored locally in `uploads/avatars` and served at the URL returned in the `avatar` field.

### Posts

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/posts?limit=20&offset=0` | List published posts |
| GET | `/api/posts/{id}` | Get a published post |
| POST | `/api/posts` | Create a post (authentication required) |
| PUT | `/api/posts/{id}` | Replace your own post (authentication required) |
| PATCH | `/api/posts/{id}` | Partially update your own post (authentication required) |
| DELETE | `/api/posts/{id}` | Delete your own post (authentication required) |

Example create-post body. The `slug`, `excerpt`, `image`, `status`, `categoryId`, `tags`, and `isFeatured` fields are optional:

```json
{
  "title": "Small Habits That Make a Big Difference",
  "content": "Full post content...",
  "slug": "small-habits-that-make-a-big-difference",
  "excerpt": "A short description",
  "image": "https://example.com/image.jpg",
  "status": "published",
  "categoryId": 3,
  "tags": ["habits", "life"],
  "isFeatured": false
}
```

Allowed `status` values are `draft`, `published`, and `archived`. If `slug` is omitted, it is generated from the title. New posts default to `draft`; public GET routes return only published posts.

### CORS for the local frontend

The backend allows requests from `http://localhost:5173`. If the frontend runs on a different origin, add its URL to `allow_origins` in `main.py`.

## Notes

- Create tables and grant database privileges in the same PostgreSQL database configured in `DATABASE_URL`.
- The `posts` table references `users.id`. The authenticated user is recorded as the author when a post is created.
- View, like, dislike, and comment counters are included in the post model, but routes for changing them are not implemented yet.
