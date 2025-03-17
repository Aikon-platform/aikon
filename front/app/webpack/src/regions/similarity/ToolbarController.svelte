<script>
import InputRangeSlider from "../../ui/InputRangeSlider.svelte";
import InputPillCheckbox from "../../ui/InputPillCheckbox.svelte";
import { appLang } from "../../constants.js";

const allowedRange = [2,6];
const params = {
    propagate: {
        recursionRange: allowedRange,
        filterByRegion: false
    }
}
///////////////////////////////////////

let setRecursionRange = (e) => params.propagate.recursionRange = e.detail;
let setFilterByRegion = (e) => params.propagate.filterByRegion = e.detail
</script>


<div>
    <div class="propagation-ctrl">
        <span><b>Propagation</b></span>
        <div class="columns is-flex is-vcentered propagation-ctrl-inputs">
            <div class="depth column is-two-thirds">
                <span>{ appLang==="fr" ? "Profondeur de récursion" : "Recursion depth" }</span>
                <InputRangeSlider minVal={2}
                                maxVal={6}
                                step={1}
                                on:updateRange={setRecursionRange}
                ></InputRangeSlider>
            </div>
            <div class="region column">
                <InputPillCheckbox checkboxLabel="Filter by region"
                                on:updateChecked={setFilterByRegion}
                ></InputPillCheckbox>
            </div>
        </div>
    </div>

</div>


<style>
.propagation-ctrl-inputs {
    margin: 10px;
    padding: 5px;
    gap: 2rem;
}
.propagation-ctrl-inputs > * {
}
</style>
