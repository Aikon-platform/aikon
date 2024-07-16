<script>
    import {manifestToMirador, refToIIIF} from "../../utils.js";
    export let qImg;
    const [wit, digit, canvas, xyhw] = qImg.split('.')[0].split('_');
    export let manifest = '';
    // export let appLang;
</script>

<tr>
    <th class="is-3 center-flex is-narrow" style="width: 260px">
        <div class="content-wrapper py-5">
            <img src="{refToIIIF(qImg, 'full', '250,')}" alt="Query region" class="mb-3 card">
            <a class="tag px-2 py-1 is-rounded is-hoverable" href="{manifestToMirador(manifest, parseInt(canvas))}" target="_blank">
                <i class="fa-solid fa-pen-to-square"></i>
                Page {parseInt(canvas)}
            </a>
            <!--TODO: add new anno button-->
        </div>
    </th>
    <td class="p-5 is-fullwidth">
        <div class="fixed-grid has-5-cols">
            <div class="grid is-gap-2">
                <slot/>
            </div>
        </div>
    </td>
</tr>
