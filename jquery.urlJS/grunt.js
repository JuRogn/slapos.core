/*global module:false*/
module.exports = function(grunt) {

	// Project configuration.
	grunt.initConfig({
		pkg: '<json:package.json>',
		meta: {
			banner: '/*! <%= pkg.title || pkg.name %> - v<%= pkg.version %> - ' +
				'<%= grunt.template.today("yyyy-mm-dd") %>\n' +
				'<%= pkg.homepage ? "* " + pkg.homepage + "\n" : "" %>' +
				'* Copyright (c) <%= grunt.template.today("yyyy") %> Nexedi;' +
				' Licensed <%= _.pluck(pkg.licenses, "type").join(", ") %> */'
		},
		concat: {
			dist: {
				src: ['<banner:meta.banner>', '<file_strip_banner:src/<%= pkg.name %>.js>'],
				dest: 'dist/<%= pkg.name %>.js'
			}
		},
		min: {
			dist: {
				src: ['<banner:meta.banner>', '<config:concat.dist.dest>'],
				dest: 'dist/<%= pkg.name %>.min.js'
			}
		},
		qunit: {
			files: ['test/**/*.html']
		},
		lint: {
			files: ['grunt.js', 'src/**/*.js', 'test/**/*.js']
		},
		watch: {
			files: '<config:lint.files>',
			tasks: 'lint qunit'
		},
		jshint: {
			options: {
				curly: true,
				eqeqeq: true,
				immed: true,
				latedef: true,
				newcap: true,
				noarg: true,
				sub: true,
				undef: true,
				boss: true,
				eqnull: true,
				browser: true
			},
			globals: {
				jQuery: true,
				Modernizr: true,
				console: true,
				unescape: true,
				// Needed to avoid "not defined error" with sinonJs
				sinon: true,
				module: true,
				test: true,
				ok: true,
				expect: true,
				stop: true,
				start: true,
				equal: true
			}
		},
		uglify: {}
	});

	// Default task.
	grunt.registerTask('default', 'lint qunit concat min');

};
