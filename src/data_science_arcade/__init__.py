from data_science_arcade.app.game import App
from data_science_arcade.progress.store import ProgressStore, real_user_save_path


def main() -> None:
    App(progress_store=ProgressStore(real_user_save_path())).run()
