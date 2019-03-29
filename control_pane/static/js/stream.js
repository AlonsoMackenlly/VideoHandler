/*//auto-updater image.src

$(function () {
    let intervalMS = 1000;
    setInterval(function () {
        let images = document.getElementsByClassName("auto-update");
        for (let i = 0; i < images.length; i++) {
            let source = images[i].src;
            $.ajax({
                url: source,
                success: function (response) {
                    if (source.indexOf("&random") !== -1)
                        source = source.substr(0, source.indexOf("&random")) + "&random=" + new Date().getTime();
                    else
                        source = source + "&random=" + new Date().getTime();

                    images[i].src = source;
                },
                error: function (xhr, status) {
                    console.log("error");
                }
            });
        }
    }, intervalMS);
});*/

function createStream() {
    let obj = {};
    obj.title = document.getElementById("modal-stream-title").value;                        //$('#modal-stream-title');
    if (obj.title === "")
        obj.title = undefined;

    obj.stream_in = document.getElementById("modal-stream-stream_in").value;                //$('#modal-stream-stream_in');
    let r = /(ftp|http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?/;
    if (!r.test(obj.stream_in)) {
        obj.stream_in = undefined;
    }
    obj.uid = parseInt(document.getElementById("modal-stream-uid").value);

    for (let key in obj)
        if (Number.isNaN(obj[key]) || obj[key] === undefined) {
            $("#modal-stream-" + key).notify('Неверное значение', {autoHideDelay: 2000, className: "warn"});
            return;
        }
    _sendJson('create', undefined, obj)
}

function actionStream(action, stream_id) {
    let title = document.getElementById('stream-title').innerHTML;
    _sendJson(action, title, undefined, stream_id);

    if (action === "delete") {
        setTimeout(function () {
            document.location.href = '/';
        }, 500);
    }
}

function actionStreams(action) {
    _sendJson(action)
}

function updateStream(stream_id) {
    let title = document.getElementById('stream-title').innerHTML;

    let obj = {};
    obj.stream_in = $("#settings-stream-stream_in").val();
    obj.uid = $("#settings-stream-uid").val();
    obj.protocol = $("#settings-stream-protocol").val();
    obj.record_path = $("#settings-stream-record_path").val();
    obj.tmp_image_path = $("#settings-stream-tmp_image_path").val();
    obj.nn_required = $("#settings-stream-nn_required").is(':checked');
    obj.telemetry_required = $("#settings-stream-telemetry_required").is(':checked');

    _sendJson('update', title, obj, stream_id)
}

function _sendJson(action = undefined, title = undefined, obj = undefined, stream_id = undefined) {
    $.ajax({
        url: window.DRONE_IP + ":" + window.VIDEO_PORT + "/api",
        data: {action: action, title: title, obj: JSON.stringify(obj), stream_id: stream_id},
        method: "GET",
        success: function (res) {
            $.notify(JSON.parse(res).message, {autoHideDelay: 2000, className: JSON.parse(res).status});
            if (action === "create") {
                $('#Modal').modal('hide');
                if (location.pathname.indexOf('/stream')===-1)
                    setTimeout(function () {
                        location.reload()
                    }, 500);
            }
        },
        error: function (xhr, status) {
            $.notify("Check console.log", {autoHideDelay: 2000, className: "error"});
            console.log("error" + xhr.toString() + " " + status.toString());
        }
    });
}