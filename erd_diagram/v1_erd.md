# ERD

```
table organizations {
  created_at timestamptz [not null, default: 'now()']
  updated_at timestamptz [not null, default: 'now()']
  deleted_at timestamptz

  id uuid [not null, pk]
  name text [not null]
}

table roles {
  created_at timestamptz [not null, default: 'now()']
  updated_at timestamptz [not null, default: 'now()']
  deleted_at timestamptz

  id uuid [not null, pk]
  name varchar [not null]
  description text
}

table divisions {
  created_at timestamptz [not null, default: 'now()']
  updated_at timestamptz [not null, default: 'now()']
  deleted_at timestamptz

  id uuid [not null, pk]
  org_id uuid [ref: > organizations.id]
  name varchar [not null]
  description text
}

table rooms {
  created_at timestamptz [not null, default: 'now()']
  updated_at timestamptz [not null, default: 'now()']
  deleted_at timestamptz

  id uuid [not null, pk]
  org_id uuid [not null, ref: - organizations.id]
  label varchar [not null]
  room_number varchar [not null]
  type varhcar [not null]
  is_booked boolean [not null]
}

table users {
  created_at timestamptz [not null, default: 'now()']
  updated_at timestamptz [not null, default: 'now()']
  deleted_at timestamptz

  id uuid [not null, pk]
  name text [not null]
  email text [not null]
  mobile_phone text
  role uuid [not null, ref: > roles.id]
  org_id uuid [ref: > organizations.id]
  division_id uuid [ref: > divisions.id]
}

table checkin_rooms {
  created_at timestamptz [not null, default: 'now()']
  updated_at timestamptz [not null, default: 'now()']
  deleted_at timestamptz

  id uuid [not null, pk]
  org_id uuid [not null, ref: > organizations.id]
  room_id uuid []
  checkin_date date
  checkin_time time
  checkout_date date
  checkout_time time
  status varchar
}

table orders {
  created_at timestamptz [not null, default: 'now()']
  updated_at timestamptz [not null, default: 'now()']
  deleted_at timestamptz

  id uuid [not null, pk]
  order_number text [not null, unique]
  session_id uuid [ref: > sessions.id]
  guest_id uuid [ref: > users.id]
  org_id uuid [ref: > organizations.id]
  category enum_order_category [not null]
  notes text
  additional_notes text
  status enum_order_status [default: 'pending']
  total_amount float [default: 0]
}

table order_items {
  created_at timestamptz [not null, default: 'now()']
  updated_at timestamptz [not null, default: 'now()']
  deleted_at timestamptz

  id uuid [not null, pk]
  order_id uuid [not null, ref: > orders.id]
  title varchar [not null]
  description text
  qty int
  price float [default: 0]
}

table sessions {
  created_at timestamptz [not null, default: 'now()']
  updated_at timestamptz [not null, default: 'now()']
  deleted_at timestamptz

  id uuid [not null, pk]
  status enum_session_status [default: 'open']
  mode enum_session_mode [default: 'agent']
  start timestamptz
  end timestamptz
  duration bigint
  session_id uuid [ref: > users.id]
  checkin_room_id uuid [ref: > checkin_rooms.id]
}

table messages {
  created_at timestamptz [not null, default: 'now()']
  updated_at timestamptz [not null, default: 'now()']
  deleted_at timestamptz

  id uuid [not null, pk]

  session_id uuid [ref: > sessions.id]
  role enum_message_role [not null]
  text text [not null]
}

enum enum_message_role {
  System
  User
}

enum enum_order_status {
  pending
  assigned
  in_progress
  completed
  rejected
  block
  suspended
}

enum enum_order_category {
  housekeeping
  room_service
  maintenance
  concierge
}

enum enum_session_status {
  open
  terminated
}

enum enum_session_mode {
  agent
  manual
}
```
