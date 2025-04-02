import React, { useContext, useEffect } from "react";
import {
    Row,
} from "antd";

import InfoPanel from "./InfoPanel";
import { ChatBox } from "./ChatBox";
import LngLatJump from "./components/LngLatJump";
import { LngLat } from "./components/type";
import Deck from "./Deck";
import { useParams } from "react-router-dom";
import { store, StoreContext } from "./store";
import { observer } from 'mobx-react-lite'
import TimelinePlayer from "./TimelinePlayer";

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
        <>
            <div className="deck">
                <Deck style={{}} />
            </div>

            <div className="left">
                <InfoPanel />
            </div>
            {(store.globalPrompt ?? "") !== "" &&
                < div className='global-prompt'>
                    <p className='global-prompt-inner'>{store.globalPrompt}</p>
                </div >
            }

            <div className='control-progress'>
                <TimelinePlayer initialInterval={1000} />
            </div>
            <Row justify="center" align="middle" style={{
                backgroundColor: "#FFFFFF",
                borderRadius: "0px 0px 16px 16px",
                boxShadow: "0px 4px 10px 0px rgba(80, 80, 80, 0.1)",
            }}>
            </Row>
            <div className="right">
                <ChatBox />
            </div>
        </>
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
