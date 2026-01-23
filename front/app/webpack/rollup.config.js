import { spawn } from 'child_process';
import del from 'rollup-plugin-delete'
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
                dedupe: ['svelte'],
                exportConditions: ['svelte'],
                extensions: ['.svelte']
            }),
            commonjs(),
            !production && livereload('public'),
            production && terser(),
            del({
                targets: ["../webapp/static/svelte/*"],
                force: true
            })  // with ES directory exports, filenames end with a hash and thus new files are created at each build rather than overwriting the old files => delete the whole `svelte/`  dir before running rollup

        ],
        watch: {
            clearScreen: false
        }
    },
    {
        input: 'src/documentSet/document-set.js',
        output: {
            sourcemap: true,
            format: 'iife',
            name: 'documentSet',
            file: '../webapp/static/svelte/documentSet.js',
            inlineDynamicImports: true
        },
        plugins: [
            svelte({
                compilerOptions: {
                    dev: !production
                }
            }),
            css({ output: 'documentSet.css' }),
            resolve({
                browser: true,
                dedupe: ['svelte'],
                exportConditions: ['svelte'],
                extensions: ['.svelte']
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
        input: 'src/witness/witness.js',
        output: {
            sourcemap: true,
            format: 'es',
            name: 'witnessView',
            dir: '../webapp/static/svelte/witnessView/',
        },
        plugins: [
            svelte({
                compilerOptions: {
                    dev: !production
                }
            }),
            css({ output: 'witness.css' }),
            resolve({
                browser: true,
                dedupe: ['svelte'],
                exportConditions: ['svelte'],
                extensions: ['.svelte']
            }),
            commonjs(),
            !production && livereload('public'),
            production && terser(),
            ],
        watch: {
            clearScreen: false
        }
    }
];
