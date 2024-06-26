<script>
    export let canvasNb;
    export let canvasImg;
    export let manifest;
    import {manifestToMirador, refToIIIF} from "../utils.js";
</script>

<tr>
    <th class="is-3 center-flex is-narrow" style="width: 260px">
        <div class="content-wrapper py-5">
            <img src="{refToIIIF(canvasImg, 'full', '250,')}" alt="Canvas {canvasNb}" class="mb-3 card">
            <div class="is-center mb-1">
                <a class="tag px-2 py-1 is-rounded" href="{manifestToMirador(manifest, canvasNb)}" target="_blank">
                    <i class="fa-solid fa-pen-to-square"></i>
                    Page {canvasNb}
                </a>
            </div>
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
