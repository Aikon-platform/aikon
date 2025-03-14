<script>
import InputRangeSlider from "../../ui/InputRangeSlider.svelte";

const allowedRange = [2,6];
$: selectedRange = allowedRange;

///////////////////////////////////////

let setSelectedRenge = (e) => selectedRange = e.detail;

</script>


<div>
    <div class="propagation-ctrl-wrapper">
        <div class="propagation-ctrl">
            <!--
                depth (range)
                current region (checkbox/pill)
            -->
            <span><b>Propagation ({ selectedRange })</b></span>
            <div class="depth">
                <InputRangeSlider minVal={2}
                                  maxVal={6}
                                  step={1}
                                  numberType="integer"
                                  on:updateRange={setSelectedRenge}
                ></InputRangeSlider>
            </div>
        </div>
    </div>

</div>


<style>

</style>
