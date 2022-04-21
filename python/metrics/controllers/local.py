from quart import Blueprint, send_from_directory, current_app

localSource = Blueprint("localSource", __name__)


@localSource.route('/store/<filename>', methods=["GET", "POST"])
async def local(filename):
    """ manage access to cached content """

    STORE_FOLDER = current_app.config["STORE_FOLDER"]
    return await send_from_directory(STORE_FOLDER, filename)