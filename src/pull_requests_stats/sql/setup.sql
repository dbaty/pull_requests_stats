create table team (
  name text primary key
);

create table person (
  login text primary key
);

create table membership (
  team_name references team(name) not null,
  person_login references person(login) not null,
  timespan daterange not null
);

create table pull_request (
  number integer primary key,
  url text not null,
  tags text[] not null default {},
  created_at timestamp not null,
  closed_at timestamp,
  updated_at timestamp not null,
  author references person(login) not null,
  dn_author_team_name references team(name)
);

create table review (
  pull_request_number references pull_request(number) not null,
  author references person(login) not null,
  dn_team_name references team(name)
);

create table comment (
  pull_request_number references pull_request(number) not null,
  author references person(login) not null,
  dn_team_name references team(name)
);
