import { spawn } from 'child_process';
import svelte from 'rollup-plugin-svelte';
import commonjs from '@rollup/plugin-commonjs';
import terser from '@rollup/plugin-terser';
import resolve from '@rollup/plugin-node-resolve';
import livereload from 'rollup-plugin-livereload';
import css from 'rollup-plugin-css-only';

const production = !process.env.ROLLUP_WATCH;

function serve() {
	let server;

	function toExit() {
		if (server) server.kill(0);
	}

	return {
		writeBundle() {
			if (server) return;
			server = spawn('npm', ['run', 'start', '--', '--dev'], {
				stdio: ['ignore', 'inherit', 'inherit'],
				shell: true
			});

			process.on('SIGTERM', toExit);
			process.on('exit', toExit);
		}
	};
}

export default [
    {
        input: 'src/regions/region-list.js',
        output: {
            sourcemap: true,
            format: 'iife',
            name: 'regionList',
            file: '../webapp/static/svelte/regionList.js'
        },
        plugins: [
            svelte({
                compilerOptions: {
                    dev: !production
                }
            }),
            css({ output: 'regionList.css' }),
            resolve({
                browser: true,
                dedupe: ['svelte']
            }),
            commonjs(),
            !production && livereload('public'),
            production && terser()
        ],
        watch: {
            clearScreen: false
        }
    },
    {
        input: 'src/records/record-list.js',
        output: {
            sourcemap: true,
            format: 'iife',
            name: 'recordList',
            file: '../webapp/static/svelte/recordList.js'
        },
        plugins: [
            svelte({
                compilerOptions: {
                    dev: !production
                }
            }),
            css({ output: 'recordList.css' }),
            resolve({
                browser: true,
                dedupe: ['svelte']
            }),
            commonjs(),
            !production && livereload('public'),
            production && terser()
        ],
        watch: {
            clearScreen: false
        }
    }
];
