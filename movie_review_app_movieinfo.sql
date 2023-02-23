-- auto-generated definition
create table movie_review_app_movieinfo
(
    id                int auto_increment
        primary key,
    movie_name        varchar(32)  not null,
    published_time    datetime(6)  not null,
    Description       longtext     not null,
    genre             varchar(32)  not null,
    movie_url         varchar(200) not null,
    admin_id_id       int          not null,
    like_list_id      int          not null,
    constraint movie_review_app_mov_admin_id_id_aa95c607_fk_movie_rev
        foreign key (admin_id_id) references movie_review_app_admininfo (id),

    constraint movie_review_app_mov_like_list_id_aed77bd2_fk_movie_rev
        foreign key (like_list_id) references movie_review_app_likelist (id)
);

