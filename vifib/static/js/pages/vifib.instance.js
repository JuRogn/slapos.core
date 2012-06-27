// SERVICES // INSTANCES
$.extend(methods, {
    showInstanceList: function (params) {
        return this.each(function () {
            var nextLevel = $.router.routes.current.level + 1,
                statusCode = {
                    401: redirect,
                    402: payment,
                    404: notFound,
                    500: serverError,
                    503: serverError
                },
                options = {
                    'title': 'My Services',
                    'mainPanel': $(this).vifib('getRender', 'instance.list'),
                    'leftbutton': {
                        'link': $(this).vifib('isAuthenticated') ? '#/dashboard' : '#/homepage',
                        'icon': 'home',
                        'title': 'Homepage'
                    },
                    'rightbutton': {
                        'link': '/instance/new',
                        'icon': 'plus',
                        'title': 'add service'
                    }
                },
                listview = $(this).vifib('render', 'instance', options).find('#instance-list');
            // Routing
            $.router.routes.add('/instance/id/:id', nextLevel, methods.showInstance, $(this));
            if (params.route !== '/instance') {
                $.router.start(params.route, nextLevel, methods.noRoute);
            } else {
                //table.vifib('refresh', methods.refreshListInstance, 30);
                $(this).slapos('instanceList', {
                    success: function (data) {
                        if (typeof (data) !== "object") {
                            data = $.parseJSON(data);
                        }
                        $.each(data.list, function () {
                            var url = this.toString(),
                                row = $('<li></li>').vifib('fillRowInstance', url);
                            //row.vifib('refresh', methods.refreshRowInstance, 30);
                            listview.append(row).listview('refresh');
                        });
                    },
                    statusCode: statusCode
                });
            }
        });
    },

    fillRowInstance: function (url) {
        return this.each(function () {
            $(this).slapos('instanceInfo', url, {
                success: function (instance) {
                    if (typeof (instance) !== "object") {
                        instance = $.parseJSON(instance);
                    }
                    $.extend(instance, {'instance_url': methods.genInstanceUrl(url)});
                    $(this).vifib('render', 'instance.listitem', instance);
                }
            });
        });
    },
    
    showInstanceRoot: function (params) {
        return this.each(function () {
            var nextLevel = $.router.routes.current.level + 1,
                options = {
                    'title': 'Service',
                    'menu': 'true',
                    'leftbutton': {
                        'link': $(this).vifib('isAuthenticated') ? '#/dashboard' : '#/homepage',
                        'icon': 'home',
                        'title': 'Homepage'
                    },
                    'menulinks': [
                        {'link': '#/instance', 'name': 'All services'}
                    ],
                };
            $(this).vifib('render', 'instance', options);
            $.router.routes.add('/instance/list', nextLevel, methods.showInstanceList, $(this).find('.content-primary'));
            $.router.routes.add('/instance/id/:id', nextLevel, methods.showInstance, $(this).find('.content-primary'));
            $.router.routes.add('/instance/id/:id/bang', nextLevel, methods.showBangInstance, $(this).find('.content-primary'));
            if ($.router.routes.isCurrent(params) === false) {
                $.router.start(params.route, nextLevel, methods.noRoute);
            }
        });
    },

    showInstance: function (params) {
        return this.each(function () {
            var statusCode = {
                401: redirect,
                402: payment,
                404: notFound,
                500: serverError
            },
                nextLevel = $.router.routes.current.level + 1;
            $(this).slapos('instanceInfo', params.id, {
                success: function (response) {
                    if (typeof (response) !== "object") {
                        response = $.parseJSON(response);
                    }
                    var content = {
                        'information': [
                            {'name': 'Reference', 'value': response.instance_id},
                            {'name': 'Status', 'value': response.status},
                            {'name': 'Software release', 'value': response.software_release},
                            {'name': 'Software type', 'value': response.software_type}
                        ],
                        'actions': [
                            {'name': 'Bang', 'link': methods.genBangUrl(params.id)},
                            {'name': 'Rename', 'link': '#/instance/rename'}
                        ]
                    };
                    //response.status = $(this).vifib('getRender', 'instance.' + response.status);
                    response.actions = [
                        {'name': "Bang", 'url': methods.genBangUrl(decodeURIComponent(params.id))}
                    ];
                    $.extend(response, content);
                    $(this).vifib('render', 'instancePanel', response);
                    //var form = $(this).find("#instance-form");
                    //form.vifib('prepareForm');
                },
                statusCode: statusCode
            });
        })
    },

    showBangInstance: function (params) {
        var statusCode = {
            400: bad_request,
            401: redirect,
            402: payment,
            404: notFound,
            500: serverError
        };
        return this.each(function () {
            console.log("plop")
            $(this).vifib('render', 'instance.bangPanel');
            $(this).find('#form-bang').submit(function () {
                var data = $(this).serializeObject(),
                    uri = methods.extractInstanceURIFromHashtag();
                $(this).slapos('instanceBang', uri, {
                    data: data,
                    statusCode: statusCode,
                    success: function () {
                        $.redirect(['instance', encodeURIComponent(uri)]);
                    }
                });
                return false;
            });
        });
    }
})