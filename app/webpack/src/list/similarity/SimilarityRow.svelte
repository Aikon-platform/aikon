<script>
    // import { similarityStore } from './similarityStore.js';
    // import {refToIIIF} from "../../utils.js";
    export let qImg;
    // export let appLang;
</script>

<tr>
    <th class="is-3 center-flex is-narrow" style="width: 260px">
        <div class="content-wrapper py-5">
            <!--<img src="{refToIIIF(canvasImg, 'full', '250,')}" alt="Canvas {canvasNb}" class="mb-3 card">-->
            {qImg}
        </div>
    </th>
    <td class="p-5 is-fullwidth">
        <div class="fixed-grid has-6-cols">
            <div class="grid is-gap-2">
                <slot/>
            </div>
        </div>
    </td>
</tr>
