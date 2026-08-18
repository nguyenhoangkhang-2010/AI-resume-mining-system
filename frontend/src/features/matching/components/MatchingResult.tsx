import {
    useMatching
} from "../hooks/useMatching";


interface Props {

    jobId:string;

}



export function MatchingResult({
    jobId
}:Props){

    const {
        data,
        isLoading,
        error
    } = useMatching(jobId);

    if(isLoading){
        return (
            <div>
                Loading matches...
            </div>
        );
    }
    if(error){
        return (
            <div>
                Failed loading matches
            </div>
        );
    }
    if(!data){
        return null;
    }


    return (
        <div>
            <h2>
                Candidate Ranking
            </h2>
            {
                data.results.map(
                    (
                        candidate,
                        index
                    )=>(
                    <div
                        key={
                            candidate
                            .candidate_profile
                            .id
                        }
                    >
                        <p>
                            Rank:
                            {index+1}
                        </p>
                        <p>
                            Score:
                            {
                            candidate
                            .similarity_score
                            }
                        </p>
                        <p>
                            Skills:
                            {
                            candidate
                            .candidate_profile
                            .skills
                            .join(", ")
                            }
                        </p>
                        <p>
                            Missing:
                            {
                            candidate
                            .skill_gaps
                            .join(", ")
                            }
                        </p>
                    </div>
                ))
            }
        </div>
    );
}