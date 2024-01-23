create table if not exists assets
(
    id               integer primary key autoincrement,
    created_at       timestamp with time zone default current_timestamp not null,
    external_user_id text                                               not null,
    external_id      text                                               not null,
    external_chat_id text                                               not null,
    storage_path     text                                               not null
);

create table if not exists chat_messages
(
    id                integer primary key autoincrement,
    created_at        timestamp with time zone default current_timestamp not null,
    text              text                                               not null,
    external_id       text                                               not null,
    external_user_id  text,
    external_chat_id  text,
    app               text                                               not null,
    external_image_id text,
    external_audio_id text,
    external_voice_id text,
    external_video_id text,
    is_forward        boolean                  default false
);

create table if not exists jobs
(
    id              integer primary key autoincrement,
    created_at      timestamp with time zone default current_timestamp not null,
    status          text                     default 'created'         not null,
    params          jsonb                                              not null,
    chat_session_id integer                                            not null references chat_sessions,
    external_id     text,
    outputs         jsonb,
    public          boolean                  default false             not null,
    app             text                                               not null,
    nsfw            boolean                  default false             not null,
    deleted_at      timestamp with time zone,
    external_status text
);

create table if not exists chat_sessions
(
    id               integer primary key autoincrement,
    created_at       timestamp with time zone default current_timestamp not null,
    logged_in_at     timestamp with time zone,
    app              text                                               not null,
    external_user_id text unique,
    context          jsonb                    default '{}',
    preferences      jsonb                    default '{}'
);
