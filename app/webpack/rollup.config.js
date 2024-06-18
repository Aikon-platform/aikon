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
    // {
    //     input: 'src/main.js',
    //     output: {
    //         sourcemap: true,
    //         format: 'iife',
    //         name: 'app',
    //         file: '../webapp/static/svelte/bundle.js'
    //     },
    //     plugins: [
    //         svelte({
    //             compilerOptions: {
    //                 dev: !production
    //             }
    //         }),
    //         css({ output: 'bundle.css' }),
    //         resolve({
    //             browser: true,
    //             dedupe: ['svelte']
    //         }),
    //         commonjs(),
    //         !production && livereload('public'),
    //         production && terser()
    //     ],
    //     watch: {
    //         clearScreen: false
    //     }
    // },
    {
        input: 'src/list/list.js',
        output: {
            sourcemap: true,
            format: 'iife',
            name: 'blockList',
            file: '../webapp/static/svelte/blockList.js'
        },
        plugins: [
            svelte({
                compilerOptions: {
                    dev: !production
                }
            }),
            css({ output: 'blockList.css' }),
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
