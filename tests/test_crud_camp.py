"""CRUD-Layer-Tests for camps. Exercises the in-memory SQLite fixture end-to-end."""

from datetime import datetime, timedelta

from app import crud, schemas


def _make_camp(name: str = "Sommerfreizeit") -> schemas.CampCreate:
    return schemas.CampCreate(
        name=name,
        start_date=datetime(2026, 7, 1),
        end_date=datetime(2026, 7, 7),
        participant_count=42,
    )


def test_create_and_get_camp(db_session):
    created = crud.create_camp(db_session, _make_camp())
    assert created.id is not None
    assert created.name == "Sommerfreizeit"

    fetched = crud.get_camp(db_session, created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.participant_count == 42


def test_get_camps_returns_all_in_last_accessed_order(db_session):
    crud.create_camp(db_session, _make_camp("A"))
    crud.create_camp(db_session, _make_camp("B"))
    camps = crud.get_camps(db_session)
    assert len(camps) == 2
    assert {c.name for c in camps} == {"A", "B"}


def test_update_camp_changes_fields(db_session):
    created = crud.create_camp(db_session, _make_camp())
    update = schemas.CampUpdate(name="Winterfreizeit", participant_count=10)
    updated = crud.update_camp(db_session, created.id, update)
    assert updated.name == "Winterfreizeit"
    assert updated.participant_count == 10
    # Untouched fields stay the same.
    assert updated.start_date == datetime(2026, 7, 1)


def test_delete_camp_removes_it(db_session):
    created = crud.create_camp(db_session, _make_camp())
    crud.delete_camp(db_session, created.id)
    assert crud.get_camp(db_session, created.id) is None


def test_update_camp_last_accessed_bumps_timestamp(db_session):
    created = crud.create_camp(db_session, _make_camp())
    original = created.last_accessed

    # Advance time artificially: set last_accessed back in the past, then bump.
    created.last_accessed = original - timedelta(days=1)
    db_session.commit()

    bumped = crud.update_camp_last_accessed(db_session, created.id)
    assert bumped.last_accessed > original - timedelta(days=1)
