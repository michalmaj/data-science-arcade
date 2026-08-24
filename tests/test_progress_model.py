from data_science_arcade.progress.model import (
    CHAPTER_COUNT,
    LESSONS_PER_CHAPTER,
    TOTAL_LESSONS,
    LessonState,
    Progress,
    chapter_of,
)


def test_total_lesson_count_matches_the_curriculum():
    assert TOTAL_LESSONS == 30
    assert CHAPTER_COUNT == 6
    assert LESSONS_PER_CHAPTER == 5


def test_chapter_of_groups_five_lessons_per_chapter():
    assert chapter_of(1) == 1
    assert chapter_of(5) == 1
    assert chapter_of(6) == 2
    assert chapter_of(30) == 6


def test_a_fresh_progress_only_unlocks_the_first_lesson():
    progress = Progress()
    assert progress.state_of(1) == LessonState.UNLOCKED
    assert progress.state_of(2) == LessonState.LOCKED
    assert progress.state_of(30) == LessonState.LOCKED


def test_unlock_only_affects_a_locked_lesson():
    progress = Progress()
    progress.lesson_states[2] = LessonState.COMPLETED

    progress.unlock(2)  # already completed - must not downgrade it
    progress.unlock(3)  # locked - becomes unlocked

    assert progress.state_of(2) == LessonState.COMPLETED
    assert progress.state_of(3) == LessonState.UNLOCKED


def test_completing_a_lesson_unlocks_the_next_one():
    progress = Progress()

    progress.complete(1)

    assert progress.state_of(1) == LessonState.COMPLETED
    assert progress.state_of(2) == LessonState.UNLOCKED


def test_completing_the_last_lesson_does_not_create_a_phantom_next_lesson():
    progress = Progress()

    progress.complete(TOTAL_LESSONS)

    assert progress.state_of(TOTAL_LESSONS) == LessonState.COMPLETED
    assert TOTAL_LESSONS + 1 not in progress.lesson_states
