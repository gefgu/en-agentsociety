import React, { useContext, useEffect } from "react";

import InfoPanel from "./LeftPanel";
import { RightPanel } from "./ChatBox";
import Deck from "./Deck";
import { useParams } from "react-router-dom";
import { store, StoreContext } from "./store";
import { observer } from 'mobx-react-lite'
import TimelinePlayer from "./TimelinePlayer";
import "./replay.css";

// const IconFont = createFromIconfontCN({
//     scriptUrl: "//at.alicdn.com/t/font_3397267_y3yy0ckhrj.js",
// });

const Replay: React.FC = observer(() => {
    const params = useParams();
    const expID = params.id;

    const store = useContext(StoreContext)

    useEffect(() => {
        store.init(expID)
    }, [expID]);

    return (
        <div className="replay-shell">
            <div className="deck">
                <Deck style={{}} />
            </div>

            <div className="agentsociety-left">
                <InfoPanel />
            </div>
            {/* {(store.globalPrompt ?? "") !== "" &&
                < div className='global-prompt'>
                    <p className='global-prompt-inner'>{store.globalPrompt}</p>
                </div >
            } */}

            <div className='control-progress'>
                <TimelinePlayer initialInterval={1000} />
            </div>
            <div className="agentsociety-right">
                <RightPanel />
            </div>
        </div>
    );
});

const Page = () => {
    return (
        <StoreContext.Provider value={store}>
            <Replay />
        </StoreContext.Provider>
    );
}

export default Page;
