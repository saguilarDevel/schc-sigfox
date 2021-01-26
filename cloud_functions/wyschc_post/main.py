from localpackage.blob_helper_functions import upload_blob
from localpackage.functions import zfill

# ====== GLOBAL VARIABLES ======


BUCKET_NAME = 'wyschc-niclabs'
SCHC_POST_URL = "https://us-central1-wyschc-niclabs.cloudfunctions.net/schc_post"
REASSEMBLER_URL = "https://us-central1-wyschc-niclabs.cloudfunctions.net/reassembler"
CLEANUP_URL = "https://us-central1-wyschc-niclabs.cloudfunctions.net/cleanup"


# ====== MAIN ======


def wyschc_post(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <http://flask.pocoo.org/docs/1.0/api/#flask.Request>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>.
    """
    if request.method == 'POST':

        # Get request JSON.
        print("POST RECEIVED")
        request_dict = request.get_json()
        print('Received Sigfox message: {}'.format(request_dict))

        upload_blob(BUCKET_NAME, zfill("Test", 8), "Test.txt")

        return '', 204

    else:
        print('Invalid HTTP Method to invoke Cloud Function. Only POST supported')
        return abort(405)
